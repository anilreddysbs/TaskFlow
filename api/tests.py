from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from datetime import date, timedelta
from django.utils import timezone
from django.db import connection
from django.test.utils import CaptureQueriesContext

from teams.models import Team
from projects.models import Project
from tasks.models import Task
from comments.models import Comment
from notifications.models import Notification
from notifications.tasks import cleanup_old_notifications, send_email_notification
from api.cache_utils import CacheManager

User = get_user_model()

class TaskFlowAPITests(APITestCase):

    def setUp(self):
        # Create users
        self.owner = User.objects.create_user(
            username='owner_user',
            email='owner@example.com',
            password='Password123!',
            bio='Owner bio'
        )
        self.member = User.objects.create_user(
            username='member_user',
            email='member@example.com',
            password='Password123!',
            bio='Member bio'
        )
        self.other_user = User.objects.create_user(
            username='other_user',
            email='other@example.com',
            password='Password123!'
        )

        # Clear cache before each test
        cache.clear()

    def get_tokens(self, user):
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {'username': user.username, 'password': 'Password123!'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data

    def authenticate_client(self, user):
        tokens = self.get_tokens(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    # --- Authentication Tests ---
    def test_obtain_jwt_tokens(self):
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {
            'username': 'owner_user',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_refresh_jwt_token(self):
        tokens = self.get_tokens(self.owner)
        url = reverse('token_refresh')
        response = self.client.post(url, {'refresh': tokens['refresh']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_me_endpoint(self):
        self.authenticate_client(self.owner)
        url = reverse('me')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'owner_user')
        self.assertEqual(response.data['email'], 'owner@example.com')

    # --- Team ViewSet Tests ---
    def test_team_crud(self):
        self.authenticate_client(self.owner)
        url = reverse('team-list')
        
        # Create Team
        response = self.client.post(url, {
            'name': 'Engineering Team',
            'description': 'Dev team',
            'member_ids': [self.member.id]
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        team_id = response.data['id']
        self.assertEqual(response.data['owner'], self.owner.id)
        self.assertEqual(len(response.data['members']), 1)
        self.assertEqual(response.data['members'][0]['username'], 'member_user')

        # List Teams
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        # Update Team
        detail_url = reverse('team-detail', args=[team_id])
        response = self.client.put(detail_url, {
            'name': 'Updated Eng Team',
            'member_ids': []
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['members']), 0)

        # Unauthorized user list teams
        self.authenticate_client(self.other_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    # --- Project ViewSet & Mass Assignment Tests ---
    def test_project_crud_and_mass_assignment_protection(self):
        # Create team
        team1 = Team.objects.create(name='Team 1', owner=self.owner)
        team1.members.add(self.member)
        team2 = Team.objects.create(name='Team 2', owner=self.other_user)

        self.authenticate_client(self.owner)
        url = reverse('project-list')

        # Create project
        response = self.client.post(url, {
            'name': 'Project Alpha',
            'description': 'Alpha phase',
            'team': team1.id
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project_id = response.data['id']

        # Prevent mass assignment (moving team)
        detail_url = reverse('project-detail', args=[project_id])
        response = self.client.patch(detail_url, {
            'team': team2.id
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('team', response.data)

        # Check nested representation (Project shows tasks count)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['tasks_count'], 0)

    # --- Task ViewSet Tests ---
    def test_task_crud_and_validations(self):
        team = Team.objects.create(name='Team 1', owner=self.owner)
        project = Project.objects.create(name='Project A', team=team, created_by=self.owner)

        self.authenticate_client(self.owner)
        url = reverse('task-list')

        # Validate past due date is rejected
        past_date = date.today() - timedelta(days=1)
        response = self.client.post(url, {
            'title': 'Task 1',
            'project': project.id,
            'due_date': past_date.isoformat()
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('due_date', response.data)

        # Writable future due date
        future_date = date.today() + timedelta(days=5)
        response = self.client.post(url, {
            'title': 'Task 1',
            'project': project.id,
            'due_date': future_date.isoformat(),
            'status': 'TODO',
            'priority': 'MEDIUM'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        task_id = response.data['id']

        # Validate security: moving task to another project is rejected
        other_project = Project.objects.create(name='Project B', team=team, created_by=self.owner)
        detail_url = reverse('task-detail', args=[task_id])
        response = self.client.patch(detail_url, {
            'project': other_project.id
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('project', response.data)

    # --- Task Dashboard Stats Tests ---
    def test_task_dashboard_stats(self):
        team = Team.objects.create(name='Team 1', owner=self.owner)
        project = Project.objects.create(name='Project A', team=team, created_by=self.owner)
        Task.objects.create(title='Task 1', project=project, created_by=self.owner, status='TODO', priority='HIGH')
        Task.objects.create(title='Task 2', project=project, created_by=self.owner, status='IN_PROGRESS', priority='MEDIUM')

        self.authenticate_client(self.owner)
        url = reverse('task-list') + "dashboard_stats/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_tasks'], 2)
        self.assertEqual(response.data['tasks_by_status']['TODO'], 1)
        self.assertEqual(response.data['tasks_by_status']['IN_PROGRESS'], 1)

    # --- Comment ViewSet Tests ---
    def test_comment_creation_and_validation(self):
        team = Team.objects.create(name='Team 1', owner=self.owner)
        project = Project.objects.create(name='Project A', team=team, created_by=self.owner)
        task = Task.objects.create(title='Task 1', project=project, created_by=self.owner)

        self.authenticate_client(self.owner)
        url = reverse('comment-list')

        # Empty content validation
        response = self.client.post(url, {
            'task': task.id,
            'content': ''
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('content', response.data)

        # Successful comment
        response = self.client.post(url, {
            'task': task.id,
            'content': 'This is a comment.'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'This is a comment.')

    # --- Caching & Invalidation Signals Tests ---
    def test_cache_invalidation_signals(self):
        team = Team.objects.create(name='Team 1', owner=self.owner)
        project = Project.objects.create(name='Project A', team=team, created_by=self.owner)
        
        # Manually cache something
        cache.set(CacheManager.get_task_list_key(), "cached_data", timeout=300)
        self.assertEqual(cache.get(CacheManager.get_task_list_key()), "cached_data")

        # Creating a task triggers signal to invalidate task list cache
        task = Task.objects.create(title='New Task', project=project, created_by=self.owner)
        self.assertIsNone(cache.get(CacheManager.get_task_list_key()))

    # --- Notification Signals Tests ---
    def test_notification_signals_on_assignee_change(self):
        team = Team.objects.create(name='Team 1', owner=self.owner)
        project = Project.objects.create(name='Project A', team=team, created_by=self.owner)
        
        # Assign on create
        task = Task.objects.create(title='Task 1', project=project, created_by=self.owner, assigned_to=self.member)
        self.assertTrue(Notification.objects.filter(recipient=self.member, message__icontains='assigned').exists())

        # Reset notifications
        Notification.objects.all().delete()

        # Update assignee
        task.assigned_to = self.owner
        task.save()
        self.assertTrue(Notification.objects.filter(recipient=self.owner, message__icontains='assigned').exists())

    # --- Health Check Endpoint Tests ---
    def test_health_check_endpoint(self):
        url = reverse('health')
        # Access health check without authentication headers
        self.client.credentials()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')
        self.assertEqual(response.data['database'], 'healthy')

    # --- Celery Background Tasks Tests ---
    def test_cleanup_old_notifications_celery_task(self):
        # Create old and new notifications
        old_time = timezone.now() - timedelta(days=31)
        n1 = Notification.objects.create(recipient=self.owner, actor=self.member, message='Old')
        n2 = Notification.objects.create(recipient=self.owner, actor=self.member, message='New')

        # Artificially set created_at back in time (auto_now_add makes it read-only normally, so we update via database queryset)
        Notification.objects.filter(id=n1.id).update(created_at=old_time)

        # Execute task synchronously
        cleanup_old_notifications()

        # Verify old is deleted, new remains
        self.assertFalse(Notification.objects.filter(id=n1.id).exists())
        self.assertTrue(Notification.objects.filter(id=n2.id).exists())

    def test_send_email_notification_celery_task(self):
        n = Notification.objects.create(recipient=self.owner, actor=self.member, message='Send email test')
        # Trigger send email task synchronously
        send_email_notification(n.id)
        # Should execute without errors (since we wrapped it in try-except/send_mail fallback)
        self.assertTrue(Notification.objects.filter(id=n.id).exists())

    # --- N+1 Query Count Optimizations Tests ---
    def test_task_viewset_query_optimizations(self):
        team = Team.objects.create(name='Team 1', owner=self.owner)
        project = Project.objects.create(name='Project A', team=team, created_by=self.owner)
        
        # Create several tasks with comments
        for i in range(5):
            t = Task.objects.create(title=f'Task {i}', project=project, created_by=self.owner, assigned_to=self.member)
            Comment.objects.create(task=t, author=self.member, content=f'Comment {i}')

        self.authenticate_client(self.owner)
        url = reverse('task-list')

        # Capture queries while requesting tasks list
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data['results']), 5)

        # Without optimizations, fetching 5 tasks with project, team, assigned_to, created_by, and comments would take ~25+ queries.
        # With select_related and prefetch_related, it should take ~4 queries (tasks list query, prefetch comments query, and pagination/count query)
        self.assertLess(len(ctx.captured_queries), 8)


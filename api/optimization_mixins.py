from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from django.db.models import Count, Q, Avg, Max, Min
from tasks.models import Task
from .cache_utils import CacheManager


class DashboardStatsView:
    """Mixin for dashboard statistics with caching and aggregation."""

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def dashboard_stats(self, request):
        """
        Return aggregated task statistics:
        - Total tasks, tasks by status, tasks by priority
        - Average tasks per project
        - Task completion metrics
        """
        cache_key = CacheManager.get_dashboard_key()
        cached = cache.get(cache_key)

        if cached:
            return Response(cached)

        user = request.user
        if user.is_superuser:
            task_qs = Task.objects.all()
        else:
            task_qs = Task.objects.filter(
                Q(project__team__owner=user) | Q(project__team__members=user)
            ).distinct()

        stats = {
            'total_tasks': task_qs.count(),
            'tasks_by_status': dict(
                task_qs.values('status').annotate(count=Count('id')).values_list('status', 'count')
            ),
            'tasks_by_priority': dict(
                task_qs.values('priority').annotate(count=Count('id')).values_list('priority', 'count')
            ),
            'avg_priority': str(task_qs.aggregate(avg=Avg('priority'))['avg'] or 0),
            'max_created_at': str(task_qs.aggregate(max_date=Max('created_at'))['max_date'] or ''),
            'min_created_at': str(task_qs.aggregate(min_date=Min('created_at'))['min_date'] or ''),
            'tasks_by_project': dict(
                task_qs.values('project__name').annotate(count=Count('id')).values_list('project__name', 'count')
            ),
        }

        cache.set(cache_key, stats, timeout=CacheManager.TIMEOUT)
        return Response(stats)


class OptimizedTaskQueryMixin:
    """Mixin for optimized Task querysets using select_related and prefetch_related."""

    def get_optimized_task_queryset(self):
        """
        Optimize task queries to prevent N+1 problems.
        
        Uses:
        - select_related('project', 'assigned_to', 'created_by') for FK relationships
        - prefetch_related('comments', 'comments__author') for reverse relationships
        """
        return (
            Task.objects
            .select_related('project', 'project__team', 'assigned_to', 'created_by')
            .prefetch_related('comments', 'comments__author')
        )


class OptimizedCommentQueryMixin:
    """Mixin for optimized Comment querysets."""

    def get_optimized_comment_queryset(self):
        """
        Optimize comment queries.
        
        Uses:
        - select_related('task', 'task__project', 'author') for FK relationships
        """
        return (
            Comment.objects
            .select_related('task', 'task__project', 'task__project__team', 'author')
        )


class OptimizedProjectQueryMixin:
    """Mixin for optimized Project querysets."""

    def get_optimized_project_queryset(self):
        """
        Optimize project queries.
        
        Uses:
        - select_related('team', 'created_by') for FK relationships
        - prefetch_related('tasks') for reverse relationships
        """
        return (
            Project.objects
            .select_related('team', 'created_by')
            .prefetch_related('tasks')
        )


class OptimizedTeamQueryMixin:
    """Mixin for optimized Team querysets."""

    def get_optimized_team_queryset(self):
        """
        Optimize team queries.
        
        Uses:
        - select_related('owner') for FK relationships
        - prefetch_related('members', 'projects') for many-to-many and reverse relationships
        """
        return (
            Team.objects
            .select_related('owner')
            .prefetch_related('members', 'projects')
        )

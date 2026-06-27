from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import models
from django.db import connection
from django.utils import timezone

from teams.models import Team
from projects.models import Project
from tasks.models import Task
from comments.models import Comment

from .serializers import TeamSerializer, ProjectSerializer, UserSerializer, TaskSerializer, CommentSerializer
from .permissions import (
    IsTeamOwner,
    IsTeamOwnerOrMemberReadOnly,
    IsProjectOwnerOrTeamMemberReadOnly,
    IsTaskCreatorOrTeamMemberReadOnly,
    IsAuthorOrTeamMemberReadOnly,
)
from .filters import TaskFilter
from .optimization_mixins import (
    DashboardStatsView,
    OptimizedTeamQueryMixin,
    OptimizedProjectQueryMixin,
    OptimizedTaskQueryMixin,
    OptimizedCommentQueryMixin,
)


class TeamViewSet(OptimizedTeamQueryMixin, ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated, IsTeamOwnerOrMemberReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return self.get_optimized_team_queryset()
        return self.get_optimized_team_queryset().filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ProjectViewSet(OptimizedProjectQueryMixin, ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, IsProjectOwnerOrTeamMemberReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return self.get_optimized_project_queryset()
        return self.get_optimized_project_queryset().filter(
            models.Q(team__owner=user) | models.Q(team__members=user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TaskViewSet(DashboardStatsView, OptimizedTaskQueryMixin, ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsTaskCreatorOrTeamMemberReadOnly]
    filterset_class = TaskFilter
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'due_date', 'priority']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return self.get_optimized_task_queryset()
        return self.get_optimized_task_queryset().filter(
            models.Q(project__team__owner=user) | models.Q(project__team__members=user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class CommentViewSet(OptimizedCommentQueryMixin, ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsAuthorOrTeamMemberReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return self.get_optimized_comment_queryset()
        return self.get_optimized_comment_queryset().filter(
            models.Q(task__project__team__owner=user) | models.Q(task__project__team__members=user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class HealthCheckView(APIView):
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            db_status = "healthy"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"

        return Response({
            'status': 'ok',
            'database': db_status,
            'timestamp': timezone.now(),
        })


from rest_framework import generics
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
User = get_user_model()
from .serializers import RegisterSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['username', 'email']



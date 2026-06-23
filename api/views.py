from django.shortcuts import render

# Create your views here.

#from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.db import models
from teams.models import Team
from projects.models import Project
from .serializers import TeamSerializer, ProjectSerializer, UserSerializer
from .permissions import IsTeamOwner
from .permissions import (
    IsTeamOwnerOrMemberReadOnly,
    IsProjectOwnerOrTeamMemberReadOnly,
    IsTaskCreatorOrTeamMemberReadOnly,
    IsAuthorOrTeamMemberReadOnly,
)
from .serializers import TaskSerializer, CommentSerializer
from .filters import TaskFilter
from tasks.models import Task
from comments.models import Comment

class TeamViewSet(ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated, IsTeamOwnerOrMemberReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Team.objects.all()
        return Team.objects.filter(models.Q(owner=user) | models.Q(members=user)).distinct()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class ProjectViewSet(ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, IsProjectOwnerOrTeamMemberReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Project.objects.all()
        return Project.objects.filter(models.Q(team__owner=user) | models.Q(team__members=user)).distinct()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TaskViewSet(ModelViewSet):
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
            return Task.objects.all()
        return Task.objects.filter(models.Q(project__team__owner=user) | models.Q(project__team__members=user)).distinct()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class CommentViewSet(ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsAuthorOrTeamMemberReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Comment.objects.all()
        return Comment.objects.filter(models.Q(task__project__team__owner=user) | models.Q(task__project__team__members=user)).distinct()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


from django.contrib.auth import get_user_model
from rest_framework import serializers
from teams.models import Team
from projects.models import Project
from tasks.models import Task
from comments.models import Comment

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')
        read_only_fields = ('id', 'username', 'email', 'first_name', 'last_name')

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email is required")
        return value

class TeamSerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True, read_only=True)
    member_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, many=True, source='members', required=False
    )

    class Meta:
        model = Team
        fields = ('id', 'name', 'description', 'owner', 'members', 'member_ids')
        read_only_fields = ('id', 'owner', 'members')

    def validate_name(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Name too short")
        return value

class ProjectSerializer(serializers.ModelSerializer):
    tasks_count = serializers.IntegerField(source='tasks.count', read_only=True)

    class Meta:
        model = Project
        fields = ('id', 'name', 'description', 'team', 'created_by', 'tasks_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')

    def validate_name(self, value):
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError("Name must be at least 3 characters long.")
        return value

    def validate(self, data):
        # Prevent mass assignment / changing team after creation
        if self.instance and 'team' in data and data['team'] != self.instance.team:
            raise serializers.ValidationError({
                'team': "Cannot change project's team after creation."
            })
        return data


class TaskSerializer(serializers.ModelSerializer):
    comment_count = serializers.IntegerField(source='comments.count', read_only=True)

    class Meta:
        model = Task
        fields = ('id', 'title', 'description', 'project', 'assigned_to', 'created_by', 'due_date', 'status', 'priority', 'comment_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')

    def validate_title(self, value):
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long")
        return value

    def validate(self, data):
        # ensure due_date is not in the past
        due = data.get('due_date')
        if due:
            from datetime import date
            if due < date.today():
                raise serializers.ValidationError({
                    'due_date': 'Due date cannot be in the past.'
                })
        
        # Prevent changing project after task creation
        if self.instance and 'project' in data and data['project'] != self.instance.project:
            raise serializers.ValidationError({
                'project': "Cannot change task's project after creation."
            })
        return data


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'task', 'author', 'content', 'created_at', 'updated_at')
        read_only_fields = ('id', 'author', 'created_at', 'updated_at')

    def validate_content(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Comment content cannot be empty.")
        if len(value) > 2000:
            raise serializers.ValidationError("Comment content too long (maximum 2000 characters).")
        return value

    def validate(self, data):
        # Prevent changing task after comment creation
        if self.instance and 'task' in data and data['task'] != self.instance.task:
            raise serializers.ValidationError({
                'task': "Cannot change comment's task."
            })
        return data
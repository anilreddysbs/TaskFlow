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

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = "__all__"
        read_only_fields = ("owner",)

    def validate_name(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Name too short")
        return value

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = "__all__"

    def validate_title(self, value):
        if not value or len(value) < 3:
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
        return data


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = "__all__"
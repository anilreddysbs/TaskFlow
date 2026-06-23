from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.db.models import Q


class IsTeamOwner(BasePermission):

    def has_object_permission(
        self,
        request,
        view,
        obj
    ):

        return obj.owner == request.user


class IsProjectTeamMember(BasePermission):
    """Allow access only to users who are members or owner of the task's project team.

    Works with Project and Task objects. For list/create actions the view
    should ensure queryset is filtered appropriately.
    """

    def has_object_permission(self, request, view, obj):
        # If obj is a Project
        team = None
        try:
            from projects.models import Project

            if isinstance(obj, Project):
                team = obj.team
        except Exception:
            pass

        # If obj is a Task
        try:
            from tasks.models import Task

            if isinstance(obj, Task):
                team = obj.project.team
        except Exception:
            pass

        if team is None:
            return False

        return team.owner == request.user or request.user in team.members.all()


class IsTeamOwnerOrMemberReadOnly(BasePermission):
    """Allow full access to team owner. Allow read-only access to team members."""

    def has_object_permission(self, request, view, obj):
        # obj is Team
        if getattr(obj, 'owner', None) == request.user:
            return True
        if request.method in SAFE_METHODS:
            return request.user in getattr(obj, 'members', []).all()
        return False


class IsProjectOwner(BasePermission):
    """Allow access if the user created the project or is the team owner."""

    def has_object_permission(self, request, view, obj):
        try:
            from projects.models import Project
            if isinstance(obj, Project):
                return obj.created_by == request.user or obj.team.owner == request.user
        except Exception:
            pass

        try:
            from tasks.models import Task
            if isinstance(obj, Task):
                return obj.project.created_by == request.user or obj.project.team.owner == request.user
        except Exception:
            pass

        return False


class IsTaskCreator(BasePermission):
    """Allow access only to the user who created the task."""

    def has_object_permission(self, request, view, obj):
        try:
            from tasks.models import Task
            if isinstance(obj, Task):
                return obj.created_by == request.user
        except Exception:
            pass
        return False


class IsProjectOwnerOrTeamMemberReadOnly(BasePermission):
    """For Project/Task objects: team members can read, owners can write."""

    def has_object_permission(self, request, view, obj):
        # determine team
        team = None
        if hasattr(obj, 'team'):
            team = obj.team
        elif hasattr(obj, 'project'):
            team = obj.project.team

        if team is None:
            return False

        if team.owner == request.user:
            return True

        if request.method in SAFE_METHODS:
            return request.user in team.members.all()

        # unsafe methods: allow if the user created the object (project/task)
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True

        return False


class IsTaskCreatorOrTeamMemberReadOnly(BasePermission):
    """For Task objects: team members can read; task creator or team owner can write."""

    def has_object_permission(self, request, view, obj):
        try:
            from tasks.models import Task
            if not isinstance(obj, Task):
                return False
        except Exception:
            return False

        team = obj.project.team
        if team.owner == request.user:
            return True

        if request.method in SAFE_METHODS:
            return request.user in team.members.all()

        if obj.created_by == request.user:
            return True

        return False


class IsAuthorOrTeamMemberReadOnly(BasePermission):
    """For Comment objects: author or team owner can modify; team members can read."""

    def has_object_permission(self, request, view, obj):
        # obj is Comment
        task = getattr(obj, 'task', None)
        if not task:
            return False
        team = task.project.team
        if team.owner == request.user:
            return True
        if request.method in SAFE_METHODS:
            return request.user in team.members.all()
        # unsafe: only author
        return getattr(obj, 'author', None) == request.user
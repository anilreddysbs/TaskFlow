from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import json


class CacheManager:
    """Centralized cache key management and invalidation."""

    TASK_LIST_KEY = "tasks:list"
    TASK_DETAIL_KEY_TEMPLATE = "tasks:detail:{id}"
    DASHBOARD_STATS_KEY = "dashboard:stats"
    TEAM_LIST_KEY_TEMPLATE = "teams:list:{user_id}"
    PROJECT_LIST_KEY_TEMPLATE = "projects:list:{user_id}"

    @staticmethod
    def get_task_list_key():
        return CacheManager.TASK_LIST_KEY

    @staticmethod
    def get_task_detail_key(task_id):
        return CacheManager.TASK_DETAIL_KEY_TEMPLATE.format(id=task_id)

    @staticmethod
    def get_dashboard_key():
        return CacheManager.DASHBOARD_STATS_KEY

    @staticmethod
    def get_team_list_key(user_id):
        return CacheManager.TEAM_LIST_KEY_TEMPLATE.format(user_id=user_id)

    @staticmethod
    def get_project_list_key(user_id):
        return CacheManager.PROJECT_LIST_KEY_TEMPLATE.format(user_id=user_id)

    @staticmethod
    def invalidate_task_caches():
        """Invalidate all task-related caches."""
        cache.delete(CacheManager.TASK_LIST_KEY)
        cache.delete(CacheManager.DASHBOARD_STATS_KEY)

    @staticmethod
    def invalidate_task_detail(task_id):
        """Invalidate specific task detail cache."""
        cache.delete(CacheManager.get_task_detail_key(task_id))

    @staticmethod
    def invalidate_team_caches(user_id):
        """Invalidate team caches for a user."""
        cache.delete(CacheManager.get_team_list_key(user_id))
        cache.delete(CacheManager.DASHBOARD_STATS_KEY)

    @staticmethod
    def invalidate_project_caches(user_id):
        """Invalidate project caches for a user."""
        cache.delete(CacheManager.get_project_list_key(user_id))
        cache.delete(CacheManager.DASHBOARD_STATS_KEY)


# Signal handlers for cache invalidation
@receiver(post_save, dispatch_uid="invalidate_task_cache_on_save")
def invalidate_task_cache_on_save(sender, instance, created, **kwargs):
    try:
        from tasks.models import Task

        if sender is Task:
            CacheManager.invalidate_task_caches()
            CacheManager.invalidate_task_detail(instance.id)
    except Exception:
        pass


@receiver(post_delete, dispatch_uid="invalidate_task_cache_on_delete")
def invalidate_task_cache_on_delete(sender, instance, **kwargs):
    try:
        from tasks.models import Task

        if sender is Task:
            CacheManager.invalidate_task_caches()
            CacheManager.invalidate_task_detail(instance.id)
    except Exception:
        pass


@receiver(post_save, dispatch_uid="invalidate_project_cache_on_save")
def invalidate_project_cache_on_save(sender, instance, **kwargs):
    try:
        from projects.models import Project

        if sender is Project:
            CacheManager.invalidate_project_caches(instance.created_by.id)
    except Exception:
        pass


@receiver(post_save, dispatch_uid="invalidate_team_cache_on_save")
def invalidate_team_cache_on_save(sender, instance, **kwargs):
    try:
        from teams.models import Team

        if sender is Team:
            CacheManager.invalidate_team_caches(instance.owner.id)
            for member in instance.members.all():
                CacheManager.invalidate_team_caches(member.id)
    except Exception:
        pass


@receiver(post_save, dispatch_uid="invalidate_comment_cache_on_save")
def invalidate_comment_cache_on_save(sender, instance, **kwargs):
    try:
        from comments.models import Comment

        if sender is Comment:
            CacheManager.invalidate_task_caches()
    except Exception:
        pass

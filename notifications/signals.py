from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
from .models import Notification

# Import lazily to avoid circular imports at import time

def _get_task_model():
    from tasks.models import Task
    return Task


def _get_comment_model():
    from comments.models import Comment
    return Comment


@receiver(pre_save, dispatch_uid="task_assignment_pre_save")
def task_pre_save(sender, instance, **kwargs):
    Task = _get_task_model()
    if sender is not Task:
        return
    if instance.pk:
        try:
            instance._old_assigned_to = Task.objects.get(pk=instance.pk).assigned_to
        except Task.DoesNotExist:
            instance._old_assigned_to = None
    else:
        instance._old_assigned_to = None


@receiver(post_save, dispatch_uid="task_assignment_notification")
def task_post_save(sender, instance, created, **kwargs):
    Task = _get_task_model()
    if sender is not Task:
        return

    # On create, if assigned_to set, notify assignee
    if created:
        if instance.assigned_to:
            Notification.objects.create(
                recipient=instance.assigned_to,
                actor=instance.created_by,
                message=f"You were assigned to task '{instance.title}'",
            )
    else:
        # On update, if assigned_to changed, notify new assignee
        old_assigned_to = getattr(instance, '_old_assigned_to', None)
        if instance.assigned_to and instance.assigned_to != old_assigned_to:
            Notification.objects.create(
                recipient=instance.assigned_to,
                actor=instance.created_by,
                message=f"You were assigned to task '{instance.title}'",
            )


@receiver(post_save, dispatch_uid="comment_notification")
def comment_post_save(sender, instance, created, **kwargs):
    Comment = _get_comment_model()
    if sender is not Comment:
        return

    if created:
        task = instance.task
        # notify task assignee and task creator (excluding comment author)
        recipients = set()
        if task.assigned_to and task.assigned_to != instance.author:
            recipients.add(task.assigned_to)
        if task.created_by and task.created_by != instance.author:
            recipients.add(task.created_by)

        for r in recipients:
            Notification.objects.create(
                recipient=r,
                actor=instance.author,
                message=f"New comment on '{task.title}': {instance.content[:100]}",
            )


@receiver(post_save, sender=Notification, dispatch_uid="send_email_notification_on_create")
def send_email_notification_on_create(sender, instance, created, **kwargs):
    if created:
        try:
            from .tasks import send_email_notification
            send_email_notification.delay(instance.id)
        except Exception:
            pass


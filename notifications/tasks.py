import logging
from celery import shared_task
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from .models import Notification

logger = logging.getLogger('taskflow')

@shared_task(bind=True, max_retries=3)
def cleanup_old_notifications(self):
    """
    Periodic task to clean up notifications older than 30 days.
    """
    try:
        cutoff = timezone.now() - timedelta(days=30)
        deleted_count, _ = Notification.objects.filter(created_at__lt=cutoff).delete()
        logger.info(f"Successfully cleaned up old notifications. Deleted count: {deleted_count}")
        return deleted_count
    except Exception as exc:
        logger.error(f"Error executing cleanup_old_notifications task: {exc}")
        self.retry(exc=exc, countdown=300)

@shared_task(bind=True, max_retries=5)
def send_email_notification(self, notification_id):
    """
    Task to send an email notification.
    """
    try:
        notification = Notification.objects.select_related('recipient', 'actor').get(id=notification_id)
        
        # Simple django email send logic
        subject = "New Notification from TaskFlow"
        body = f"Hello {notification.recipient.username},\n\n{notification.message}\n\nBest,\nTaskFlow Team"
        
        send_mail(
            subject=subject,
            message=body,
            from_email=None,  # Uses DEFAULT_FROM_EMAIL setting
            recipient_list=[notification.recipient.email],
            fail_silently=False,
        )
        logger.info(f"Successfully sent email notification to {notification.recipient.email}")
    except Notification.DoesNotExist:
        logger.warning(f"Notification with id {notification_id} does not exist. Skipping.")
    except Exception as exc:
        logger.error(f"Error sending email notification {notification_id}: {exc}")
        self.retry(exc=exc, countdown=60)

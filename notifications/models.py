from django.db import models
from django.conf import settings

# Create your models here.
class Notification(models.Model):
	recipient = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='notifications'
	)

	actor = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='sent_notifications'
	)

	message = models.CharField(max_length=255)
	read = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Notification to {self.recipient} - {self.message}"

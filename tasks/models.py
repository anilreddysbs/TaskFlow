from django.db import models
from projects.models import Project
from taskflow import settings

# Create your models here.
class Task(models.Model):
    class StatusChoices(models.TextChoices):
        TODO = "TODO", "To Do"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        DONE = "DONE", "Done"
        BLOCKED = "BLOCKED", "Blocked"
    class PriorityChoices(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"
    title=models.CharField(max_length=255)
    description=models.TextField(blank=True,null=True)
    project=models.ForeignKey(Project,on_delete=models.CASCADE,related_name="tasks")
    assigned_to=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name="assigned_tasks")
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="created_tasks")
    due_date=models.DateField(null=True,blank=True)
    status=models.CharField(max_length=20,choices=StatusChoices.choices,default=StatusChoices.TODO)
    priority=models.CharField(max_length=20,choices=PriorityChoices.choices,default=PriorityChoices.MEDIUM)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.title
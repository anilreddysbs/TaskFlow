from django.db import models
from teams.models import Team
from users.models import User
from django.conf import settings

# Create your models here.
class Project(models.Model):
    name=models.CharField(max_length=100)
    description=models.TextField(blank=True,null=True)
    team=models.ForeignKey(Team,on_delete=models.CASCADE,related_name='projects')
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='created_projects')
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
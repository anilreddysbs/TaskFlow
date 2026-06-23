from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
    email=models.EmailField(unique=True)
    bio=models.TextField(blank=True,null=True)
    created_at=models.DateTimeField(auto_now_add=True)



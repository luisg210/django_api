from django.db import models

# Create your models here.
class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    done = models.BooleanField(default=False)
    username = models.CharField(max_length=200) 
    created_at = models.DateTimeField(auto_now_add=True) 

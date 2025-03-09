from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Student(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    roll_number = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    is_nominated = models.BooleanField(default=False)
    has_voted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.roll_number})"

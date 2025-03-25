from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.student_id})"
    
    def save(self, *args, **kwargs):
        if not self.user.username:
            # Create username from first name and last name
            self.user.username = f"{self.user.first_name.lower()}{self.user.last_name.lower()}"
        super().save(*args, **kwargs)

class HOD(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.OneToOneField(Department, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.department.name}"

class Officer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()}"

class ClassLeaderNomination(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('finalized', 'Finalized'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    nomination_text = models.TextField(help_text="Why do you want to be a class leader?")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    feedback = models.TextField(blank=True, null=True, help_text="HOD's feedback on the nomination")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_by = models.ForeignKey(HOD, on_delete=models.SET_NULL, null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    finalized_by = models.ForeignKey(Officer, on_delete=models.SET_NULL, null=True, blank=True)
    finalized_at = models.DateTimeField(null=True, blank=True)
    finalization_notes = models.TextField(blank=True, null=True, help_text="Officer's notes on finalization")

    class Meta:
        unique_together = ['student', 'department']

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.department.name}"

    def save(self, *args, **kwargs):
        if not self.department:
            self.department = self.student.department
        super().save(*args, **kwargs)

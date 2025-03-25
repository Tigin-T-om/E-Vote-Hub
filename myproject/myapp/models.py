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
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female')
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M')  # Set default to 'M'
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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

class VotingSession(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('published', 'Published'),
        ('cancelled', 'Cancelled')
    ]
    
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    created_by = models.ForeignKey(Officer, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    results_verified = models.BooleanField(default=False)
    
    def is_active(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date and self.status == 'active'

    def can_be_removed(self):
        return self.status in ['scheduled', 'active']

    def __str__(self):
        return f"Voting Session for {self.department.name} ({self.start_date} - {self.end_date})"


class Candidate(models.Model):
    nomination = models.OneToOneField(ClassLeaderNomination, on_delete=models.CASCADE)
    voting_session = models.ForeignKey(VotingSession, on_delete=models.CASCADE)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female')])
    vote_count = models.IntegerField(default=0)

class Vote(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    voting_session = models.ForeignKey(VotingSession, on_delete=models.CASCADE)
    male_candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='male_votes')
    female_candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='female_votes')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'voting_session']

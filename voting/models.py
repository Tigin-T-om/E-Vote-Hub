from django.db import models
from django.contrib.auth.models import AbstractUser

# 1. Department (e.g., MCA, BCA)
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True) # e.g., MCA

    def __str__(self):
        return self.code

# 2. Batch (The Private Class Room)
class Batch(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    year = models.IntegerField() # 1, 2, 3
    section = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C')]) 

    class Meta:
        unique_together = ('department', 'year', 'section')

    def __str__(self):
        return f"{self.department.code} - Year {self.year} - {self.section}"

# 3. Custom User (Student/HOD)
class User(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('cr', 'Class Representative'),
        ('hod', 'HOD'),
        ('officer', 'Presiding Officer'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Security Features
    is_password_changed = models.BooleanField(default=False)
    face_encoding = models.BinaryField(null=True, blank=True)
    
    # Voting Status
    has_voted_phase1 = models.BooleanField(default=False) # For Class Rep
    has_voted_phase2 = models.BooleanField(default=False) # For Council

# 4. Candidate (Who is running)
class Candidate(models.Model):
    POST_CHOICES = [
        ('CR_MALE', 'Class Rep (Male)'),
        ('CR_FEMALE', 'Class Rep (Female)'),
        ('CHAIRMAN', 'Chairman'),
    ]
    student = models.OneToOneField(User, on_delete=models.CASCADE)
    post = models.CharField(max_length=20, choices=POST_CHOICES)
    manifesto = models.TextField()
    photo = models.ImageField(upload_to='candidates/')
    
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.username} - {self.post}"

# 5. The Vote (Secret)
class Vote(models.Model):
    voter_hash = models.CharField(max_length=255)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
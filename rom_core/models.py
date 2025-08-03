from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('clinician', 'Clinician'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    unique_code = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"

class ROMTest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    flexion = models.FloatField()
    extension = models.FloatField()
    abduction = models.FloatField()
    adduction = models.FloatField()

    def __str__(self):
        return f"{self.user.username} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class Exercise(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField()
    image = models.ImageField(upload_to='exercises/', null=True, blank=True)
    video_url = models.URLField(blank=True, null=True)  # Optional, for YouTube or similar

    def __str__(self):
        return self.name

class ExerciseCompletion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    date = models.DateField()

    def __str__(self):
        return f"{self.user.username} - {self.exercise.name} ({self.date})"

class RehabSchedule(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    exercises = models.ManyToManyField(Exercise)

    def __str__(self):
        return f"{self.user.username} - {self.date} ({self.exercises.count()} exercises)"
    
class RehabSessionFeedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    pain_level = models.PositiveSmallIntegerField()
    feedback = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.date} (Pain: {self.pain_level})"

class ROMWarning(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    warning_type = models.CharField(max_length=64)  # e.g., "External Rotation Low"
    details = models.TextField(blank=True)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

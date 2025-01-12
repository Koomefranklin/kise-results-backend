from django.db import models
from dev.models import User
import uuid

# Create your models here.

class Section(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  name = models.CharField(max_length=200)
  contribution = models.IntegerField()
  created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='section_created_by')
  updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='section_updated_by', null=True, blank=True)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

class Aspect(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  name = models.CharField(max_length=200)
  section = models .ForeignKey(Section, on_delete=models.CASCADE)
  contribution = models.IntegerField()
  created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='aspect_created_by')
  updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='aspect_updated_by', null=True, blank=True)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

class Student(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  user = models.ForeignKey(User, on_delete=models.CASCADE)
  department = models.CharField(max_length=50)
  index = models.IntegerField()
  school = models.CharField(max_length=200)
  grade = models.IntegerField()
  learning_area = models.CharField(max_length=200)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

class StudentLetter(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  student = models.ForeignKey(Student, on_delete=models.CASCADE)
  assessor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessor')
  total_score = models.FloatField()
  comments = models.CharField(max_length=255)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

class StudentSection(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  student_letter = models.ForeignKey(StudentLetter, on_delete=models.CASCADE)
  section = models.ForeignKey(Section, on_delete=models.CASCADE)
  score = models.FloatField()
  comments = models.CharField(max_length=255)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

class StudentAspect(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  student_section = models.ForeignKey(StudentSection, on_delete=models.CASCADE)
  aspect = models.ForeignKey(Aspect, on_delete=models.CASCADE)
  score = models.FloatField()
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

class Location(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  student_letter = models.ForeignKey(StudentLetter, on_delete=models.CASCADE)
  latitude = ()
  longitude = ()
  created_at = models.DateTimeField(auto_now_add=True)

from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
  ROLES = [
    ('student', 'Student'),
    ('lecturer', 'Lecturer'),
  ]
  surname = models.CharField(max_length=50)
  other_names = models.CharField(max_length=100)
  first_name = None
  last_name = None
  role = models.CharField(choices=ROLES, max_length=10, default='student')
  REQUIRED_FIELDS = ['surname', 'other_names', ]

  def __str__(self):
    return f'{self.surname} {self.other_names}'
  
class Session(models.Model):

  class Period(models.IntegerChoices):
    First = 1
    Second = 2

  class Mode(models.TextChoices):
    DISTANCE_LEARNING = 'DL'
    FULL_TIME = 'FT'
    COMMON = 'CM'

  period = models.IntegerField(choices=Period.choices)
  mode = models.CharField(max_length=2, choices=Mode.choices)

  def __str__(self):
    return f'{self.mode} Year {self.period}'

class Lecturer(models.Model):
  class Role(models.TextChoices):
    TEAM_LEADER = 'TL'
    LECTURER = 'LEC'

  user = models.ForeignKey(User, on_delete=models.CASCADE)
  role = models.CharField(max_length=3, choices=Role.choices, default=Role.LECTURER)

  class Meta:
    constraints = [
      models.UniqueConstraint(fields=['user',], name='unique_lecturer_user'),
    ]

  def __str__(self):
    return str(self.user)

class Student(models.Model):
  admission = models.CharField(max_length=20, primary_key=True)
  user = models.ForeignKey(User, on_delete=models.CASCADE)
  year = models.DateField()
  session = models.CharField(max_length=50)

  class Meta:
    constraints = [
      models.UniqueConstraint(fields=['user',], name='unique_student_user'),
    ]

  def __str__(self):
    return f'{self.admission} {self.user.surname}'

class Course(models.Model):
  code = models.IntegerField(primary_key=True)
  name = models.CharField(max_length=50)
  session = models.ForeignKey(Session, on_delete=models.CASCADE)

  def __str__(self):
    return f'{self.code} {self.name}'

class Paper(models.Model):
  code = models.CharField(max_length=8, primary_key=True)
  name = models.CharField(max_length=100)
  course = models.ForeignKey(Course, on_delete=models.CASCADE)

  def __str__(self):
    return f'{self.code} {self.name}'

class TeamLeader(models.Model):
  lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE)
  course = models.ForeignKey(Course, on_delete=models.CASCADE)

  class Meta:
    constraints = [
      models.UniqueConstraint(fields=['lecturer',], name='unique_teamleader'),
    ]

  def __str__(self):
    return str(self.lecturer)

class Specialization(models.Model):
  student = models.ForeignKey(Student, on_delete=models.CASCADE)
  course = models.ForeignKey(Course, on_delete=models.CASCADE)

  class Meta:
    constraints = [
      models.UniqueConstraint(fields=['student', 'course'], name='unique_student_course'),
    ]

  def __str__(self):
    return str(self.student)
  
class Module(models.Model):
  code = models.CharField(max_length=10, primary_key=True)
  name = models.CharField(max_length=200)
  paper = models.ForeignKey(Paper, on_delete=models.CASCADE)

  def __str__(self):
    return str(f'{self.code} {self.name}')

class CatCombination(models.Model):
  cat1 = models.ManyToManyField(Module, related_name='cat1')
  cat2 = models.ManyToManyField(Module, related_name='cat2')
  paper = models.ForeignKey(Paper, on_delete=models.CASCADE)

  def __str__(self):
    return str(self.paper)

class LecturerModule(models.Model):
  lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE)
  module = models.ForeignKey(Module, on_delete=models.CASCADE)
  period = models.CharField(max_length=50)

class Result(models.Model):
  student = models.ForeignKey(Student, on_delete=models.CASCADE)
  paper = models.ForeignKey(Paper, on_delete=models.CASCADE)
  cat1 = models.IntegerField(null=True, blank=True)
  cat2 = models.IntegerField(null=True, blank=True)
  session = models.CharField(max_length=50)

  class Meta:
    constraints = [
      models.UniqueConstraint(fields=['student', 'paper', 'session'], name='unique_student_session_result')
    ]

  def __str__(self):
    return str(f'{self.student} {self.paper}')

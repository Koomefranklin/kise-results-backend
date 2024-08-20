from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.utils.translation import gettext_lazy as _

# Create your models here.

class User(AbstractUser):
  class Role(models.TextChoices):
    STUDENT = 'student', _('Student')
    LECTURER = 'lecturer', _('Lecturer')
    ADMIN = 'admin', _('Admin')

  class Sex(models.TextChoices):
    MALE = 'M', _('Male')
    FEMALE = 'F', _('Female')

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  full_name = models.CharField(max_length=200)
  first_name = None
  last_name = None
  sex = models.CharField(max_length=2, choices=Sex.choices)
  role = models.CharField(choices=Role.choices, max_length=10, default=Role.STUDENT)

  REQUIRED_FIELDS = ['full_name', 'sex', 'role']

  def save(self, *args, **kwargs):
    self.full_name = self.full_name.capitalize()
    super().save(*args, **kwargs)

  def __str__(self):
    return f'{self.full_name}'
  
class Session(models.Model):

  class Period(models.IntegerChoices):
    First = 1
    Second = 2

  class Mode(models.TextChoices):
    DL = 'DL', _('Distance Learning')
    FT = 'FT', _('Full Time')
    CM = 'CM', _('Common')

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  period = models.IntegerField(choices=Period.choices)
  mode = models.CharField(max_length=2, choices=Mode.choices)

  def __str__(self):
    return f'{self.mode} Year {self.period}'

class Student(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  admission = models.CharField(max_length=20, unique=True)
  user = models.ForeignKey(User, on_delete=models.CASCADE)
  session = models.ForeignKey(Session, on_delete=models.CASCADE)
  centre = models.CharField(max_length=20)

  class Meta:
    constraints = [
      models.UniqueConstraint(fields=['user',], name='unique_student_user'),
    ]

  def save(self, *args, **kwargs):
    self.admission = self.admission.upper()
    super().save(*args, **kwargs)

  def __str__(self):
    return f'{self.admission} {self.user.full_name}'

class Course(models.Model):
  code = models.IntegerField(primary_key=True)
  name = models.CharField(max_length=50)
  session = models.ForeignKey(Session, on_delete=models.CASCADE)

  def __str__(self):
    return f'{self.code} {self.name}'
  
class Lecturer(models.Model):
  class Role(models.TextChoices):
    TEAM_LEADER = 'HoD'
    LECTURER = 'Lecturer'


  user = models.ForeignKey(User, on_delete=models.CASCADE)
  role = models.CharField(max_length=10, choices=Role.choices, default=Role.LECTURER)
  department = models.ForeignKey(Course, on_delete=models.CASCADE)

  class Meta:
    constraints = [
      models.UniqueConstraint(fields=['user',], name='unique_lecturer_user'),
    ]

  def __str__(self):
    return str(self.user)

class Paper(models.Model):
  code = models.CharField(max_length=8, primary_key=True)
  name = models.CharField(max_length=100)
  course = models.ForeignKey(Course, on_delete=models.CASCADE)

  def __str__(self):
    return f'{self.code} {self.name}'

class TeamLeader(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE)
  department = models.ForeignKey(Course, on_delete=models.CASCADE)

  class Meta:
    constraints = [
      models.UniqueConstraint(fields=['lecturer',], name='unique_teamleader'),
    ]

  def __str__(self):
    return str(self.lecturer)

class Specialization(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  student = models.ForeignKey(Student, related_name='student_results', on_delete=models.CASCADE)
  paper = models.ForeignKey(Paper, on_delete=models.CASCADE)
  cat1 = models.IntegerField(null=True, blank=True)
  cat2 = models.IntegerField(null=True, blank=True)

  class Meta:
    constraints = [
      models.UniqueConstraint(fields=['student', 'paper'], name='unique_student_result')
    ]

  def __str__(self):
    return str(f'{self.student} {self.paper}')
  
class IndexNumber(models.Model):
  student = models.ForeignKey(Student, on_delete=models.CASCADE)
  index = models.CharField(max_length=100, primary_key=True)

  def save(self, *args, **kwargs):
    index = self.index
    self.index = int(f'20407101{index:03d}')
    super().save(*args, **kwargs)

  def __str__(self):
    return f'{str(self.student)} : {str(self.index)}'
  
class ModuleScore(models.Model):
  student = models.ForeignKey(Student, related_name='student_index', on_delete=models.CASCADE)
  module = models.ForeignKey(Module, on_delete=models.CASCADE)
  score = models.IntegerField()

  class Meta:
    constraints = [
      models.UniqueConstraint(fields=['student', 'module'], name='unique_student_module')
    ]
  
  def __str__(self):
    return f'{self.student} : {self.module}'

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
    self.full_name = self.full_name.upper()
    super().save(*args, **kwargs)

  def __str__(self):
    return f'{self.full_name}'
  
class Mode(models.Model):
  class MODE(models.TextChoices):
    DL = 'DL', _('Distance Learning')
    FT = 'FT', _('Full Time')
    CM = 'CM', _('Common')

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  mode = models.CharField(max_length=2, choices=MODE.choices)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return f'{self.mode}'
  
class Centre(models.Model):
  class CENTRES(models.TextChoices):
    KISE = 'KISE', _('KISE Main Centre')
    MIGORI = 'Migori', _('Migori Centre')
    SHIMO = 'Shimo', _('Shimo La Tewa Centre')
    KERICHO = 'Kericho', _('Kericho')
    EREGI = 'Eregi', _('Eregi Centre')

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  name = models.CharField(max_length=50, choices=CENTRES.choices)

  def __str__(self):
    return f'{self.name}'

class Course(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  code = models.IntegerField()
  name = models.CharField(max_length=50)
  mode = models.ForeignKey(Mode, on_delete=models.CASCADE, related_name='course_mode')
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return f'{self.code} {self.name}'
  def save(self, *args, **kwargs):
    self.name = self.name.upper()
    super().save(*args, **kwargs)

class Paper(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  code = models.CharField(max_length=8)
  name = models.CharField(max_length=100)
  course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course')
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return f'{self.code} {self.name}'

  def save(self, *args, **kwargs):
    self.name = self.name.upper()
    super().save(*args, **kwargs)

class Student(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  admission = models.CharField(max_length=20, unique=True)
  user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_details')
  mode = models.ForeignKey(Mode, on_delete=models.CASCADE, related_name='study_mode')
  centre = models.ForeignKey(Centre, on_delete=models.CASCADE, related_name='student_centre')
  added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='added_by')
  updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_change', null=True, blank=True)
  course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='student_course')
  year = models.DateField()
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def save(self, *args, **kwargs):
    self.admission = self.admission.upper()
    super().save(*args, **kwargs)

  def __str__(self):
    return f'{self.admission} {self.user.full_name}'
  
class IndexNumber(models.Model):
  student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='student')
  index = models.CharField(max_length=100, primary_key=True)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def save(self, *args, **kwargs):
    index = self.index
    self.index = int(f'20407101{index:03d}')
    super().save(*args, **kwargs)

  def __str__(self):
    return f'{str(self.student)} : {str(self.index)}'
  
class Lecturer(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lecturer_details')
  courses = models.ManyToManyField(Course, related_name='lecturer_courses')
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    constraints = [
      models.UniqueConstraint(fields=['user',], name='unique_lecturer_user'),
    ]

  def __str__(self):
    return str(self.user)
  
class Hod(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name='hod_lecturer')
  department = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='hod_department')
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    constraints = [
      models.UniqueConstraint(fields=['lecturer',], name='unique_hod'),
    ]

  def __str__(self):
    return str(self.lecturer)

class TeamLeader(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name='tl_lecturer')
  centre = models.ForeignKey(Centre, on_delete=models.CASCADE, related_name='tl_centre')
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    constraints = [
      models.UniqueConstraint(fields=['lecturer',], name='unique_teamleader'),
    ]

  def __str__(self):
    return str(self.lecturer)
  
class Module(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  code = models.CharField(max_length=10)
  name = models.CharField(max_length=200)
  paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name='module_paper')
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return str(f'{self.code} {self.name}')

class CatCombination(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  cat1 = models.ManyToManyField(Module, related_name='cat1')
  cat2 = models.ManyToManyField(Module, related_name='cat2')
  paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name='combination_paper')
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return str(self.paper)
  
class ModuleScore(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  student = models.ForeignKey(Student, related_name='student_score', on_delete=models.CASCADE)
  module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='score_module')
  discussion = models.IntegerField()
  take_away = models.IntegerField()
  added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='score_add')
  created_at = models.DateTimeField(auto_now_add=True)
  updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='score_change', null=True, blank=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    constraints = [
      models.UniqueConstraint(fields=['student', 'module'], name='unique_student_module')
    ]
  
  def __str__(self):
    return f'{self.student} : {self.module}'
  
class SittingCat(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  student = models.ForeignKey(Student, related_name='student_scat', on_delete=models.CASCADE)
  paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name='sitting_paper')
  cat1 = models.IntegerField()
  cat2 = models.IntegerField()
  added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cat_add')
  created_at = models.DateTimeField(auto_now_add=True)
  updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sitting_change', null=True, blank=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return self.student
  
class Result(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  student = models.ForeignKey(Student, related_name='student_results', on_delete=models.CASCADE)
  paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name='result_paper')
  cat1 = models.IntegerField(null=True, blank=True)
  cat2 = models.IntegerField(null=True, blank=True)
  added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='result_add')
  created_at = models.DateTimeField(auto_now_add=True)
  updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='result_change', null=True, blank=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    constraints = [
      models.UniqueConstraint(fields=['student', 'paper'], name='unique_student_result')
    ]

  def __str__(self):
    return str(f'{self.student} {self.paper}')

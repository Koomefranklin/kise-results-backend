from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

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
  sex = models.CharField(max_length=2, choices=Sex.choices, null=True, blank=True)
  role = models.CharField(choices=Role.choices, max_length=10, default=Role.STUDENT)

  REQUIRED_FIELDS = ['full_name', 'sex', 'role']

  class Meta:
    ordering = ['full_name']

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
  code = models.CharField(max_length=10)
  name = models.CharField(max_length=200)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return self.name

class Specialization(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_specialization')
  code = models.IntegerField()
  name = models.CharField(max_length=50)
  mode = models.ForeignKey(Mode, on_delete=models.CASCADE, related_name='specialization_mode')
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
  specialization = models.ForeignKey(Specialization, on_delete=models.CASCADE, related_name='specialization')
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    ordering = ['code']

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
  specialization = models.ForeignKey(Specialization, on_delete=models.CASCADE, related_name='student_specialization')
  year = models.DateField()
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    ordering = ['admission']

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
  specializations = models.ManyToManyField(Specialization, related_name='lecturer_specializations')
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    order_with_respect_to = 'user'
    constraints = [
      models.UniqueConstraint(fields=['user',], name='unique_lecturer_user'),
    ]

  def __str__(self):
    return str(self.user)
  
class Hod(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name='hod_lecturer')
  department = models.ForeignKey(Specialization, on_delete=models.CASCADE, related_name='hod_department')
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

  class Meta:
    order_with_respect_to = 'paper'
    constraints = [
      models.UniqueConstraint(fields=['paper',], name='unique_paper_combination')
    ]

  def __str__(self):
    return str(self.paper)
  
class ModuleScore(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  student = models.ForeignKey(Student, related_name='student_score', on_delete=models.CASCADE)
  module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='score_module')
  discussion = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(10)])
  take_away = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(10)])
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
  
class SitinCat(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  student = models.ForeignKey(Student, related_name='student_scat', on_delete=models.CASCADE)
  paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name='sitin_paper')
  cat1 = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(60)])
  cat2 = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(60)])
  added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cat_add')
  created_at = models.DateTimeField(auto_now_add=True)
  updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sitin_change', null=True, blank=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    constraints = [
      models.UniqueConstraint(fields=['student', 'paper'], name='unique_student_paper')
    ]

  def __str__(self):
    return self.student
  
class Result(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  student = models.ForeignKey(Student, related_name='student_results', on_delete=models.CASCADE)
  paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name='result_paper')
  cat1 = models.FloatField(null=True, blank=True)
  cat2 = models.FloatField(null=True, blank=True)
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
  
class Deadline(models.Model):
  class NAMES(models.TextChoices):
    TAKEAWAY = 'takeaway', _('Takeaway')
    DISSCUSSION = 'discussion', _('Discussion')
    CAT1 = 'cat1', _('Sit-in Cat 1')
    CAT2 = 'cat2', _('Sit-in Cat 2')

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  name = models.CharField(max_length=15, choices=NAMES.choices, default=NAMES.TAKEAWAY, unique=True)
  deadline = models.DateTimeField()
  created_at = models.DateTimeField(auto_now_add=True)
  added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deadline_add')
  updated_at = models.DateTimeField(auto_now=True)
  updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deadline_edit', null=True, blank=True)

  class Meta:
    constraints = [
      models.UniqueConstraint(fields=['name'], name='unique_deadline')
    ]
  
  def __str__(self):
      return f'{self.name} {self.deadline}'
    
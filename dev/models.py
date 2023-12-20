from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
  ROLES = [
    ('student', 'Student'),
    ('lecturer', 'Lecturer'),
  ]
  sirname = models.CharField(max_length=50)
  other_names = models.CharField(max_length=100)
  first_name = None
  last_name = None
  role = models.CharField(choices=ROLES, max_length=10, default='student')
  REQUIRED_FIELDS = ['sirname', 'other_names', ]

  def __str__(self):
    return f'{self.sirname} {self.other_names}'
  
class Session(models.Model):

  class Year(models.IntegerChoices):
    First = 1
    Second = 2

  class Mode(models.TextChoices):
    DISTANCE_LEARNING = 'DL'
    FULL_TIME = 'FT'

  year = models.IntegerField(choices=Year.choices)
  mode = models.CharField(max_length=2, choices=Mode.choices)

class Lecturer(models.Model):
  class Role(models.TextChoices):
    TEAM_LEADER = 'TL'
    LECTURER = 'LEC'

  user = models.ForeignKey(User, on_delete=models.CASCADE)
  role = models.CharField(max_length=3, choices=Role.choices, default=Role.LECTURER)


from django.db import models
from dev.models import User
import uuid
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from geopy.geocoders import Nominatim
from geopy.exc import GeopyError
from django.utils.translation import gettext_lazy as _

# Create your models here.

class ZonalLeader(models.Model):
  class ZONES(models.TextChoices):
    KISE_A = 'KISE A', _('KISE A')
    KISE_B = 'KISE B', _('KISE B')
    KISE_C = 'KISE C', _('KISE C')
    KISE_NAIROBI_KAJIADO_EAST = 'KISE-NAIROBI/KAJIADO EAST', _('KISE-NAIROBI/KAJIADO EAST')
    KISE_NAIROBI_KAJIADO_WEST = 'KISE-NAIROBI/KAJIADO WEST', _('KISE-NAIROBI/KAJIADO WEST')
    EREGI = 'EREGI', _('EREGI')
    MIGORI = 'MIGORI', _('MIGORI')
    KERICHO_A = 'KERICHO A', _('KERICHO A')
    KERICHO_B = 'KERICHO B', _('KERICHO B')
    SHANZU = 'SHANZU', _('SHANZU')

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  zone_name = models.CharField(max_length=200, choices=ZONES.choices)
  assessor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='zonal_leader')
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return self.zone_name

class Section(models.Model):
  class AssessmentType(models.TextChoices):
    GENERAL = 'General', _('General')
    PHE = 'PHE', _('Physical Health Education')

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  number = models.IntegerField()
  name = models.CharField(max_length=200)
  contribution = models.IntegerField()
  assessment_type = models.CharField(max_length=50, choices=AssessmentType.choices)
  created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='section_created_by')
  updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='section_updated_by', null=True, blank=True)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    ordering = ['number']

  def __str__(self):
    return f'{self.name} - {self.assessment_type}'
  
class SubSection(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='sub_section')
  name = models.CharField(max_length=200)
  contribution = models.IntegerField()
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return f'{self.section.name} - {self.name}'
  
  class Meta:
    order_with_respect_to = 'section'

class Aspect(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  name = models.CharField(max_length=200)
  section = models .ForeignKey(Section, on_delete=models.CASCADE)
  sub_section = models.ForeignKey(SubSection, on_delete=models.CASCADE, related_name='aspect_sub_section', null=True, blank=True)
  contribution = models.IntegerField()
  is_active = models.BooleanField(default=True)
  created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='aspect_created_by')
  updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='aspect_updated_by', null=True, blank=True)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return self.name
  
  class Meta:
    order_with_respect_to = 'section'

class Student(models.Model):
  class Sex(models.TextChoices):
    MALE = 'M', _('Male')
    FEMALE = 'F', _('Female')

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  full_name = models.CharField(max_length=200)
  sex = models.CharField(max_length=2, choices=Sex.choices)
  index = models.CharField(blank=True, null=True, max_length=50, verbose_name='Assessment Number')
  email = models.EmailField(max_length=200, null=True, blank=True)
  period = models.DateField(null=True, blank=True)
  created_by = models.ForeignKey(User, related_name='created_by', null=True, blank=True, on_delete=models.RESTRICT)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return self.full_name

class Location(gis_models.Model):
  name = models.CharField(max_length=255, blank=True)
  point = gis_models.PointField(srid=4326)  # Using WGS 84 coordinate system
  address = models.TextField(blank=True, null=True)
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return self.name or f"Location at {self.address}"
  
  def google_maps_url(self):
    if self.point:
      return f"https://www.google.com/maps?q={self.point.y},{self.point.x}"
    return None

  def get_address(self):
    if self.point:
      geolocator = Nominatim(user_agent="geoapi")
      location = geolocator.reverse((self.point.y, self.point.x), language='en')
      return location.address if location else "Address not found"
    return "No point data"
  
  def save(self, *args, **kwargs):
    if not self.name and self.point:
      self.address = f'{self.point.y}, {self.point.x}'
      print(self.address)
      try:
        geolocator = Nominatim(user_agent="geoapi")
        location = geolocator.reverse((self.point.y, self.point.x), language='en')  # (latitude, longitude)
        self.name = location.address if location else "Unknown Location"
      except GeopyError:
        self.name = "Error fetching address"

    super().save(*args, **kwargs)

class StudentLetter(models.Model):
  class ZONES(models.TextChoices):
    KISE_A = 'KISE A', _('KISE A')
    KISE_B = 'KISE B', _('KISE B')
    KISE_C = 'KISE C', _('KISE C')
    KISE_NAIROBI_KAJIADO_EAST = 'KISE-NAIROBI/KAJIADO EAST', _('KISE-NAIROBI/KAJIADO EAST')
    KISE_NAIROBI_KAJIADO_WEST = 'KISE-NAIROBI/KAJIADO WEST', _('KISE-NAIROBI/KAJIADO WEST')
    EREGI = 'EREGI', _('EREGI')
    MIGORI = 'MIGORI', _('MIGORI')
    KERICHO_A = 'KERICHO A', _('KERICHO A')
    KERICHO_B = 'KERICHO B', _('KERICHO B')
    SHANZU = 'SHANZU', _('SHANZU')

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  student = models.ForeignKey(Student, on_delete=models.CASCADE)
  department = models.CharField(max_length=50, null=True, blank=True)
  school = models.CharField(max_length=200, null=True, blank=True)
  grade = models.CharField(null=True, blank=True, verbose_name='Grade/Level', max_length=50)
  learning_area = models.CharField(max_length=200, null=True, blank=True)
  assessor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessor')
  total_score = models.IntegerField(default=0)
  comments = models.CharField(max_length=255, blank=True, null=True, verbose_name='General Comments and Suggestions:')
  zone = models.CharField(max_length=200, null=True, blank=True, choices=ZONES.choices)
  location = models.ForeignKey(Location, on_delete=models.CASCADE)
  late_submission = models.BooleanField(default=False)
  reason = models.CharField(max_length=255, blank=True, null=True, verbose_name='Reason for late submission')
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def save(self, *args, **kwargs):
    request = kwargs.pop('request', None)

    if request and hasattr(request, 'user') and hasattr(request.user, 'location'):
      # If user has a location associated with their profile
      self.location = request.user.location 
    elif request and request.GET.get('allow_location', False) == 'true':
      # Check if user has granted location permission
      if 'geolocation' in request.headers:
        geolocation = request.headers.get('geolocation')
        try:
          latitude, longitude = map(float, geolocation.split(','))
          point = Point(longitude, latitude)  # Note: Longitude, Latitude order
          try:
            location = Location.objects.get(point=point)
          except Location.DoesNotExist:
            location = Location.objects.create(point=point)
          self.location = location
        except (ValueError, IndexError):
          pass  # Handle invalid geolocation data

    super().save(*args, **kwargs)

  def __str__(self):
    return self.student.full_name

class StudentSection(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  student_letter = models.ForeignKey(StudentLetter, on_delete=models.CASCADE, related_name='student_sections')
  section = models.ForeignKey(Section, on_delete=models.CASCADE)
  score = models.IntegerField(default=0)
  comments = models.CharField(max_length=255, null=True)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return f'{self.student_letter.student.full_name} {self.section.name}'
  
  class Meta:
    order_with_respect_to = 'section'

class StudentAspect(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  student_section = models.ForeignKey(StudentSection, on_delete=models.CASCADE, related_name='student_aspects')
  aspect = models.ForeignKey(Aspect, on_delete=models.CASCADE)
  score = models.IntegerField(default=0)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return f'{self.student_section.student_letter.student.full_name} {self.aspect.name}'
  
  class Meta:
    order_with_respect_to = 'aspect'

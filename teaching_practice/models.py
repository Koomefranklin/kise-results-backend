from django.db import models
from dev.models import User
import uuid
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from geopy.geocoders import Nominatim
from geopy.exc import GeopyError
from django.utils.translation import gettext_lazy as _

# Create your models here.

class Section(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  number = models.IntegerField()
  name = models.CharField(max_length=200)
  contribution = models.IntegerField()
  created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='section_created_by')
  updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='section_updated_by', null=True, blank=True)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    ordering = ['number']

  def __str__(self):
    return self.name
  
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
  department = models.CharField(max_length=50)
  index = models.IntegerField()
  school = models.CharField(max_length=200)
  grade = models.IntegerField()
  learning_area = models.CharField(max_length=200)
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
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  student = models.ForeignKey(Student, on_delete=models.CASCADE)
  assessor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessor')
  total_score = models.FloatField(default=0)
  comments = models.CharField(max_length=255, blank=True, null=True)
  location = models.ForeignKey(Location, on_delete=models.CASCADE)
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
  student_letter = models.ForeignKey(StudentLetter, on_delete=models.CASCADE)
  section = models.ForeignKey(Section, on_delete=models.CASCADE)
  score = models.FloatField(default=0)
  comments = models.CharField(max_length=255, null=True)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return f'{self.student_letter.student.user.full_name} {self.section.name}'

class StudentAspect(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  student_section = models.ForeignKey(StudentSection, on_delete=models.CASCADE, related_name='student_aspects')
  aspect = models.ForeignKey(Aspect, on_delete=models.CASCADE)
  score = models.FloatField(default=0)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return f'{self.student_section.student_letter.student.user.full_name} {self.aspect.name}'

from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.shortcuts import get_object_or_404, redirect

from dev.models import Hod
from teaching_practice.models import AssessmentType, Period, ZonalLeader

class AdminMixin:
  def has_permission(self):
    user = self.request.user
    assessment_types = AssessmentType.objects.all()
    admins = assessment_types.values_list('admins', flat=True)
    return user.is_superuser or user.id in admins
  
  def handle_no_permission(self):
    return redirect('no_permission')

  def dispatch(self, request, *args, **kwargs):
    if not self.has_permission():
      raise PermissionDenied
    return super().dispatch(request, *args, **kwargs)
  
class ActivePeriodMixin:      
  lookup_field = 'is_active'

  def dispatch(self, request, *args, **kwargs):

    if not Period.objects.filter(**{self.lookup_field: True}).exists():
      raise PermissionDenied("Action not allowed at this Period")
    
    return super().dispatch(request, *args, **kwargs)
  
class AdminHeadMixin:
  def has_permission(self):
    user = self.request.user
    hod_ids = Hod.objects.all().values_list('lecturer__user__pk', flat=True)
    admin_ids = AssessmentType.objects.all().values_list('admins', flat=True)
    zonal_leader_ids = ZonalLeader.objects.all().values_list('assessor', flat=True)
    return user.is_superuser or user.id in hod_ids or user.id in admin_ids or user.id in zonal_leader_ids
  
  def handle_no_permission(self):
    return redirect('no_permission')
  
  def dispatch(self, request, *args, **kwargs):
    if not self.has_permission():
      raise PermissionDenied
    return super().dispatch(request, *args, **kwargs)
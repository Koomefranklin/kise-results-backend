from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.shortcuts import get_object_or_404, redirect

from teaching_practice.models import Period

class AdminMixin:
  def has_permission(self):
    user = self.request.user
    return user.is_staff
  
  def handle_no_permission(self):
    return redirect('no_permission')

  def dispatch(self, request, *args, **kwargs):
    if not self.has_permission():
      raise PermissionDenied
    return super().dispatch(request, *args, **kwargs)
  
class ActivePeriodMixin:
  model = Period          
  lookup_field = 'is_active'

def dispatch(self, request, *args, **kwargs):

  if not self.model.objects.filter(**{self.lookup_field: True}).exists():
    raise PermissionDenied("Action not allowed at this Period")
  
  return super().dispatch(request, *args, **kwargs)
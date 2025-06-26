from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from dev.models import Hod

class AdminMixin:
  def has_permission(self):
    user = self.request.user
    return user.role == 'admin'
  
  def handle_no_permission(self):
    return redirect('no_permission')

  def dispatch(self, request, *args, **kwargs):
    if not self.has_permission():
      raise PermissionDenied
    return super().dispatch(request, *args, **kwargs)
  
class AdminOrLecturerMixin:
  def has_permission(self):
    user = self.request.user
    return False if user.role == 'student' else True
  
  def handle_no_permission(self):
    return redirect('no_permission')

  def dispatch(self, request, *args, **kwargs):
    if not self.has_permission():
      raise PermissionDenied
    return super().dispatch(request, *args, **kwargs)
  
class AdminOrHeadMixin:
  def has_permission(self):
    user = self.request.user
    hod = Hod.objects.filter(lecturer__user=user).first()
    return True if user.role == 'admin' or hod else False
  
  def handle_no_permission(self):
    return redirect('no_permission')

  def dispatch(self, request, *args, **kwargs):
    if not self.has_permission():
      raise PermissionDenied
    return super().dispatch(request, *args, **kwargs)
  
class HoDMixin:
  def has_permission(self):
    user = self.request.user
    hod = Hod.objects.filter(lecturer__user=user).first()
    return True if user.is_superuser or hod else False
  
  def handle_no_permission(self):
    return redirect('no_permission')

  def dispatch(self, request, *args, **kwargs):
    if not self.has_permission():
      raise PermissionDenied
    return super().dispatch(request, *args, **kwargs)
  
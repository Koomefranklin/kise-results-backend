from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

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
    return False if user.role == 'student' else True
  
  def handle_no_permission(self):
    return redirect('no_permission')

  def dispatch(self, request, *args, **kwargs):
    if not self.has_permission():
      raise PermissionDenied
    return super().dispatch(request, *args, **kwargs)
  
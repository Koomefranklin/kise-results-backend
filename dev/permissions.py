from rest_framework import permissions
from .models import Lecturer

class IsLecturer(permissions.BasePermission):
  message = 'user is not a lecturer'

  def has_permission(self, request, view):
    user = request.user
    return user.role == 'lecturer' or user.role == 'admin'
  
class IsHod(permissions.BasePermission):
  message = 'user is not a Head of Department'

  def has_permission(self, request, view):
    if request.method in permissions.SAFE_METHODS:
      return True
    user = request.user
    return Lecturer.objects.get(user=user).role == 'HoD'
  
class IsStudent(permissions.BasePermission):
  message = 'user is not a student'

  def has_permission(self, request, view):
    user = request.user
    return user.role == 'student'

class ReadOnly(permissions.BasePermission):
  def has_permission(self, request, view):
    if request.method in permissions.SAFE_METHODS:
      return True

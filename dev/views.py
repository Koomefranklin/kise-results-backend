from django.shortcuts import render
from django.db.models import Q
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import User

# Create your views here.

# def get_context_data(self, **kwargs):
#     context = super().get_context_data(**kwargs)
#     context['has_permission'] = self.request.user
#     context['units'] = RegisteredUnit.objects.filter(student__user=self.request.user)
#     context['student_details'] = Student.objects.get(user=self.request.user)
#     return context

class IndexPage(LoginRequiredMixin, ListView):
  template_name = 'results/index.html'
  context_object_name = 'context'
  model = User

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['has_permission'] = self.request.user
    context['is_student'] = True if self.request.user.role == 'student' else False
    context['is_lecturer'] = not context['is_student']
    return context

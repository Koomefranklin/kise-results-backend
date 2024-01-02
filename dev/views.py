from django.shortcuts import render
from django.db.models import Q
from django.views.generic import ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import User, Student, Result, Session, Lecturer, Course, Paper, TeamLeader,Specialization, Module, CatCombination, LecturerModule
from .forms import ResultForm, StudentPaperUpdateForm
from dal import autocomplete
from django.urls import reverse_lazy

# Create your views here.

class StudentAutocomplete(autocomplete.Select2QuerySetView):
  def get_queryset(self):
    qs = Student.objects.all()
    if self.q:
      qs = qs.filter(Q(user__surname__icontains=self.q) | Q(user__other_names__icontains=self.q) | Q(admission__icontains=self.q))
    return qs

class IndexPage(LoginRequiredMixin, ListView):
  template_name = 'results/index.html'
  context_object_name = 'context'
  model = Paper
  queryset = Paper.objects.all()

  # def get_queryset(self):
  #   user = self.request.user
  #   queryset = Paper.objects.all()
  #   return queryset

  def get_context_data(self, **kwargs):
    user = self.request.user
    context = super().get_context_data(**kwargs)
    context['has_permission'] = user
    context['is_student'] = True if user.role == 'student' else False
    context['is_lecturer'] = not context['is_student']
    context['y1'] = self.queryset.filter(course__session__period=1).all()
    context['dly2'] = self.queryset.filter(Q(course__session__period=2) & Q(course__session__mode='DL')).all()
    context['fty2'] = self.queryset.filter(Q(course__session__period=2) & Q(course__session__mode='FT')).all()
    context['is_tl'] = TeamLeader.objects.get(lecturer__user=user)
    return context

class PaperResult(LoginRequiredMixin, ListView):
  model = Result
  template_name = 'results/paper_result.html'
  context_object_name = 'students'
  paginate_by = 50


  def get_queryset(self):
    user = self.request.user
    # units = LecturerUnit.objects.filter(lecturer__user=user).values('unit')
    # if self.kwargs.get('unit', None):
    #   reg_units = RegisteredUnit.objects.filter(Q(unit__in=units) & Q(unit=self.kwargs['unit'])).all()
    # else:
    #   reg_units = RegisteredUnit.objects.filter(unit__in=units).all()
    
    queryset = Result.objects.filter(paper__pk=self.kwargs['paper']).all().order_by('cat1')
    search_query = self.request.GET.get('query')
    query =  Q(student__user__surname__icontains=search_query) | Q(student__user__other_names__icontains=search_query) | Q(student__admission__icontains=search_query)
    if search_query:
      queryset = queryset.filter(query).order_by('cat1')
    return queryset
  
  def get_context_data(self, **kwargs):
    lecturer = Lecturer.objects.get(user=self.request.user)
    context = super().get_context_data(**kwargs)
    context['has_permission'] = self.request.user
    context['form'] = ResultForm(self)
    context['total'] = Result.objects.all().count()
    context['is_nav_sidebar_enabled'] = True
    context['is_lecturer'] = lecturer
    context['paper'] = Paper.objects.get(pk=self.kwargs['paper'])
    # context['lecturer_units'] = LecturerUnit.objects.filter(lecturer__user=self.request.user).values_list('unit', flat=True)
    return context
  
  def post(self, request, *args, **kwargs):
    form = ResultForm(self, request.POST)
    form.initial['paper'] = Paper.objects.get(pk=self.kwargs.get('paper'))
    if form.is_valid():
      form.save()
    return self.get(request, *args, **kwargs)
  
class StudentResult(LoginRequiredMixin, ListView):
  model = Result
  template_name = 'results/student_result.html'
  context_object_name = 'results'
  queryset = Result.objects.all()

  def get_context_data(self, **kwargs):
    user = self.request.user
    context = super().get_context_data(**kwargs)
    context['is_student'] = True if user.role == 'student' else False
    context['has_permission'] = user
    if user.role == 'student':
      context['y1'] = self.queryset.filter(Q(student__user=user) & Q(paper__course__session__period=1)).all()
      context['y2'] = self.queryset.filter(Q(student__user=user) & Q(paper__course__session__period=2)).all()
      context['course1'] = Course.objects.get(session__mode='CM')
      context['course2'] = Specialization.objects.get(student__user=user)
    else:
      context['is_nav_sidebar_enabled'] = True
    return context
  
class CourseResults(LoginRequiredMixin, ListView):
  model = Result
  template_name = 'results/course_results.html'
  context_object_name = 'results'

  def get_queryset(self):
    user = self.request.user
    course = TeamLeader.objects.get(lecturer__user=user).course
    papers = Paper.objects.filter(course=course)
    results = Result.objects.filter(paper__in=papers)
    return results
  
  def get_context_data(self, **kwargs):
    user = self.request.user
    context = super().get_context_data(**kwargs)
    context['has_permission'] = user
    context['is_student'] = True if user.role == 'student' else False
    context['is_lecturer'] = not context['is_student']
    context['is_tl'] = TeamLeader.objects.get(lecturer__user=user)
    context['is_nav_sidebar_enabled'] = True
    return context
  
class StudentPaperUpdate(LoginRequiredMixin, UpdateView):
  model = Result
  template_name = 'results/result_update.html'
  form_class = StudentPaperUpdateForm

  def get_success_url(self):
    paper = Result.objects.get(pk=self.kwargs['pk']).paper.pk
    return reverse_lazy('single_paper', kwargs={'paper':paper})

  def get_context_data(self, **kwargs):
    user = self.request.user
    context = super().get_context_data(**kwargs)
    context['has_permission'] = user
    context['is_student'] = True if user.role == 'student' else False
    context['is_lecturer'] = not context['is_student']
    context['is_tl'] = TeamLeader.objects.get(lecturer__user=user)
    context['is_nav_sidebar_enabled'] = True
    context['details'] = Result.objects.get(pk=self.kwargs['pk'])
    return context
  

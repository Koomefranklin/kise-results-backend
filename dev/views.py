from typing import Any
from django.db.models.query import QuerySet
from django.shortcuts import render
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import ModuleScore, User, Student, Result, Session, Lecturer, Course, Paper, TeamLeader,Specialization, Module, CatCombination, LecturerModule, IndexNumber
from django.http.response import HttpResponse
from itertools import chain
from rest_framework import response, viewsets, views
from .serializers import ModuleScoreSerializer, UserSerializer, StudentSerializer, StudentViewSerializer, ResultCreateSerializer, StudentResultSerializer, CourseSerializer, PaperSerializer, SpecializationSerializer, LecturerSerializer, SessionSerializer, KnecIndexNumberSerializer
from rest_framework.permissions import IsAuthenticated
from .permissions import IsLecturer, IsStudent, IsHod, ReadOnly

# Create your views here.

class CommonVariables:
  inderdisciplinary = 9101

class ScoreViewSet(viewsets.ModelViewSet):
  queryset = ModuleScore.objects.all()
  serializer_class = ModuleScoreSerializer
  permission_classes=[IsLecturer]

class UserViewSet(viewsets.ModelViewSet):
  queryset = User.objects.all()
  permission_classes = [IsAuthenticated]
  serializer_class = UserSerializer
  def get_queryset(self):
    userId = self.request.user.id
    return User.objects.filter(id=userId)
     
class StudentViewSet(viewsets.ModelViewSet):
  queryset = Student.objects.all()
  serializer_class = StudentViewSerializer
  # permission_classes = [IsHod]
  def get_queryset(self):
    user = self.request.user
    if user.role == 'lecturer':
      course = Lecturer.objects.get(user = user).department
      students = Specialization.objects.filter(Q(course=course) | Q(course__code=CommonVariables.inderdisciplinary)).values_list('student', flat=True)
      return Student.objects.filter(pk__in=students)
    elif user.role == 'admin':
      return Student.objects.all()
    else:
      return HttpResponse('You dont have permision to view this')

class ResultsViewSet(viewsets.ModelViewSet):
  queryset = Result.objects.all()
  serializer_class = StudentResultSerializer
  permission_classes = [IsAuthenticated]
  def get_queryset(self):
    user = self.request.user
    if user.role == 'lecturer':
      course = Lecturer.objects.get(user=user).department
      papers = Paper.objects.filter(Q(course=course) | Q(course__code=CommonVariables.inderdisciplinary)).values_list('code', flat=True)
      return Result.objects.filter(paper__code__in=papers)
    elif user.role == 'admin':
      return Result.objects.all()
    else:
      return HttpResponse('You dont have permision to view this')
  
class ResultsListView(viewsets.ModelViewSet):
  queryset = Student.objects.all()
  serializer_class = StudentResultSerializer
  permission_classes = [ReadOnly]
  # def get_queryset(self):
  #   user = self.request.user
  #   if user.role == 'lecturer':
  #     course = Lecturer.objects.get(user=user).department
  #     papers = Paper.objects.filter(Q(course=course) | Q(course__code=CommonVariables.inderdisciplinary)).values_list('code', flat=True)
  #     return Result.objects.filter(paper__code__in=papers)
  #   elif user.role == 'admin':
  #     return Result.objects.all()
  #   else:
  #     return HttpResponse('You dont have permision to view this')

class CourseViewSet(viewsets.ModelViewSet):
  queryset = Course.objects.all()
  serializer_class = CourseSerializer
  permission_classes = [IsAuthenticated]
  def get_queryset(self):
    user = self.request.user
    if user.role == 'admin':
      return Course.objects.all()
    elif user.role == 'lecturer':
      course_id = Lecturer.objects.get(user = user).department.code
      first = CommonVariables.inderdisciplinary
      return Course.objects.filter(Q(pk=course_id) | Q(pk=first))
    elif user.role == 'student':
      course_id = Specialization.objects.get(student__user = user).course.code
      return Course.objects.filter(pk=course_id)
  
class PaperViewSet(viewsets.ModelViewSet):
  queryset = Paper.objects.all()
  serializer_class = PaperSerializer
  permission_classes = [IsAuthenticated]
  def get_queryset(self):
    user = self.request.user
    if user.role =='lecturer':
      course = Lecturer.objects.get(user=user).department
      return Paper.objects.filter(Q(course=course) | Q(course__code=CommonVariables.inderdisciplinary))
    elif user.role == 'admin':
      return Paper.objects.all()
    else:
      return HttpResponse('You dont have permision to view this')
  
class SpecializationViewSet(viewsets.ModelViewSet):
  queryset = Specialization.objects.all()
  serializer_class = SpecializationSerializer
  permission_classes = [IsLecturer]
  def get_queryset(self):
    user = self.request.user
    if user.role =='lecturer':
      course = Lecturer.objects.get(user = user).department
      return Specialization.objects.filter(Q(course=course) | Q(course__code=CommonVariables.inderdisciplinary))
    elif user.role == 'admin':
      return Specialization.objects.all()
    else:
      return HttpResponse('You dont have permision to view this')
    
class LecturerViewSet(viewsets.ModelViewSet):
  queryset = Lecturer.objects.all()
  serializer_class = LecturerSerializer
  permission_classes = [IsLecturer]

  def get_queryset(self):
    user = self.request.user
    if user.role == 'lecturer':
      lecturer_role = Lecturer.objects.get(user=user).role
      if lecturer_role == 'HoD':
        department = Lecturer.objects.get(user=user).department
        return Lecturer.objects.filter(department=department)
      else:
        return Lecturer.objects.filter(user=user)
    elif user.role =='admin':
      return Lecturer.objects.all()
    else:
      return HttpResponse('You dont have permision to view this')

class SessionViewSet(viewsets.ModelViewSet):
  queryset = Session.objects.all()
  serializer_class = SessionSerializer
  permission_classes = [IsAuthenticated]

  def get_queryset(self):
    user = self.request.user
    if user.role == 'admin':
      return Session.objects.all()
    else:
      if user.role == 'lecturer':
        course = Lecturer.objects.get(user = user).department
      elif user.role == 'student':
        course = Specialization.objects.get(student__user = user).course
      session_id = course.session.pk
      return Session.objects.filter(Q(pk=session_id) | Q(period='1'))
  
class KnecIndexViewSet(viewsets.ModelViewSet):
  queryset = IndexNumber.objects.all()
  serializer_class = KnecIndexNumberSerializer
  permission_classes = [IsAuthenticated]
  

class StatisticsView(views.APIView):
  permission_classes = [IsAuthenticated]

  def get(self, request):
    user = self.request.user
    if user.role == 'lecturer':
      courses = 2
      course1 = Lecturer.objects.get(user=user).department.code
      course2 = CommonVariables.inderdisciplinary
      papers = Paper.objects.filter(Q(course__pk=course1) | Q(course__pk=course2)).count()
      students = Specialization.objects.filter(Q(course__pk = course1) | Q(course__pk = course2)).count()
      results = Result.objects.count()
      return response.Response({'courses': courses, 'papers': papers, 'students': students, 'results': results})
    elif user.role == 'admin':
      courses = Course.objects.count()
      papers = Paper.objects.count()
      students = Specialization.objects.count()
      results = Result.objects.count()
      lecturers = Lecturer.objects.count()
      return response.Response({'courses': courses, 'papers': papers, 'students': students, 'results': results, 'lecturers': lecturers})   

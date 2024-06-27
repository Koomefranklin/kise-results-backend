from typing import Any
from django.db.models.query import QuerySet
from django.shortcuts import render
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import ModuleScore, User, Student, Result, Session, Lecturer, Course, Paper, TeamLeader,Specialization, Module, CatCombination, LecturerModule, KnecIndexNumber
from django.http.response import HttpResponse
from itertools import chain
from rest_framework import generics, viewsets, views
from .serializers import ModuleScoreSerializer, UserSerializer, StudentSerializer, StudentViewSerializer, ResultCreateSerializer, ResultSerializer, CourseSerializer, PaperSerializer, SpecializationSerializer, LecturerSerializer, SessionSerializer, KnecIndexNumberSerializer
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
  permission_classes = [IsHod]
  def get_queryset(self):
    user = self.request.user
    if user.role == 'lecturer':
      course = Lecturer.objects.get(user = user).department
      students = Specialization.objects.filter(course=course).values_list('student', flat=True)
      return Student.objects.filter(pk__in=students)
    elif user.role == 'admin':
      return Student.objects.all()
    else:
      return HttpResponse('You dont have permision to view this')

class ResultsViewSet(viewsets.ModelViewSet):
  queryset = Result.objects.all()
  serializer_class = ResultCreateSerializer
  permission_classes = [IsLecturer]
  def get_queryset(self):
    user = self.request.user
    if user.role == 'lecturer':
      course = Lecturer.objects.get(user=user).department
      papers = Paper.objects.filter(course=course).values_list('code', flat=True)
      return Result.objects.filter(paper__code__in=papers)
    elif user.role == 'admin':
      return Result.objects.all()
    else:
      return HttpResponse('You dont have permision to view this')
  
class ResultsListView(viewsets.ModelViewSet):
  queryset = Result.objects.all()
  serializer_class = ResultSerializer
  permission_classes = [ReadOnly]
  def get_queryset(self):
    user = self.request.user
    course = Lecturer.objects.get(user=user).department
    papers = Paper.objects.filter(course=course).values_list('code', flat=True)
    return Result.objects.filter(paper__code__in=papers)

class CourseViewSet(viewsets.ModelViewSet):
  queryset = Course.objects.all()
  serializer_class = CourseSerializer
  permission_classes = [IsLecturer]
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
  permission_classes = [IsLecturer]
  def get_queryset(self):
    user = self.request.user
    course = Lecturer.objects.get(user=user).department
    return Paper.objects.filter(course=course)
  
class SpecializationViewSet(viewsets.ModelViewSet):
  queryset = Specialization.objects.all()
  serializer_class = SpecializationSerializer
  permission_classes = [IsLecturer]
  def get_queryset(self):
    user = self.request.user
    course = Lecturer.objects.get(user = user).department
    return Specialization.objects.filter(course=course)
  
class LecturerViewSet(viewsets.ModelViewSet):
  queryset = Lecturer.objects.all()
  serializer_class = LecturerSerializer
  permission_classes = [IsLecturer]

  def get_queryset(self):
    user = self.request.user
    lecturer_role = Lecturer.objects.get(user=user).role
    if lecturer_role == 'HoD':
      department = Lecturer.objects.get(user=user).department
      return Lecturer.objects.filter(department=department)
    else:
      return Lecturer.objects.filter(user=user)
    

class SessionViewSet(viewsets.ModelViewSet):
  queryset = Session.objects.all()
  serializer_class = SessionSerializer
  permission_classes = [IsAuthenticated]

  def get_queryset(self):
    user = self.request.user
    if user.role == 'lecturer':
      course = Lecturer.objects.get(user = user).department
    elif user.role == 'student':
      course = Specialization.objects.get(student__user = user).course
    session_id = course.session.pk
    return Session.objects.filter(Q(pk=session_id) | Q(period='1'))
  
class KnecIndexViewSet(viewsets.ModelViewSet):
  queryset = KnecIndexNumber.objects.all()
  serializer_class = KnecIndexNumberSerializer
  permission_classes = [IsAuthenticated]
  

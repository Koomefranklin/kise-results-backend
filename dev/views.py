from typing import Any
from django.db.models.query import QuerySet
from django.shortcuts import render
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import ModuleScore, User, Student, Result, Mode, Lecturer, Course, Paper, TeamLeader, Module, CatCombination, IndexNumber, SittingCat, Centre
from django.http.response import HttpResponse
from itertools import chain
from rest_framework import response, viewsets, views
from .serializers import UserSerializer
from .serializers import ModuleScoreSerializer, UserSerializer, StudentSerializer, StudentViewSerializer, ResultCreateSerializer, StudentResultSerializer, CourseSerializer, PaperSerializer, LecturerSerializer, ModeSerializer, KnecIndexNumberSerializer, SittingCatSerializer, ModuleSerializer, CentreSerializer
from rest_framework.permissions import IsAuthenticated
from .permissions import IsLecturer, IsStudent, IsHod, ReadOnly

# Create your views here.

class ModuleScoreViewSet(viewsets.ModelViewSet):
  queryset = ModuleScore.objects.all()
  serializer_class = ModuleScoreSerializer
  permission_classes=[IsAuthenticated]

class SittingCatViewSet(viewsets.ModelViewSet):
  queryset = SittingCat.objects.all()
  serializer_class = SittingCatSerializer
  permission_classes = [IsAuthenticated]

class UserViewSet(viewsets.ModelViewSet):
  queryset = User.objects.all()
  permission_classes = [IsAuthenticated]
  serializer_class = UserSerializer
  def get_queryset(self):
    userId = self.request.user.id
    return User.objects.filter(id=userId)
     
class StudentViewSet(viewsets.ModelViewSet):
  queryset = Student.objects.all()
  serializer_class = StudentSerializer
  permission_classes = [IsAuthenticated]
  def get_queryset(self):
    user = self.request.user
    if user.role == 'lecturer':
      courses = Lecturer.objects.get(user = user).courses
      students = Student.objects.filter(course_in=courses).values_list('student', flat=True)
      return Student.objects.filter(pk__in=students)
    elif user.role == 'admin':
      return Student.objects.all()
    else:
      return HttpResponse('You dont have permision to view this')
    
class StudentListViewSet(viewsets.ModelViewSet):
  queryset = Student.objects.all()
  serializer_class = StudentViewSerializer
  permission_classes = [IsAuthenticated]


class ResultsViewSet(viewsets.ModelViewSet):
  queryset = Result.objects.all()
  serializer_class = StudentResultSerializer
  permission_classes = [IsAuthenticated]
  def get_queryset(self):
    user = self.request.user
    if user.role == 'lecturer':
      courses = Lecturer.objects.get(user=user).courses
      papers = Paper.objects.filter(course_in=courses).values_list('code', flat=True)
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
      courses = Lecturer.objects.get(user = user).courses
      return Course.objects.filter(pk_in=courses)
    elif user.role == 'student':
      course_id = Student.objects.get(student__user = user).course.code
      return Course.objects.filter(pk=course_id)
  
class PaperViewSet(viewsets.ModelViewSet):
  queryset = Paper.objects.all()
  serializer_class = PaperSerializer
  permission_classes = [IsAuthenticated]
  def get_queryset(self):
    user = self.request.user
    if user.role =='lecturer':
      courses = Lecturer.objects.get(user=user).courses
      return Paper.objects.filter(course_in=courses)
    elif user.role == 'admin':
      return Paper.objects.all()
    else:
      return HttpResponse('You dont have permision to view this')
    
class ModuleViewSet(viewsets.ModelViewSet):
  queryset = Module.objects.all()
  serializer_class = ModuleSerializer
  permission_classes = [IsAuthenticated]
    
class CentreViewSet(viewsets.ModelViewSet):
  queryset = Centre.objects.all()
  serializer_class = CentreSerializer
  permission_classes = [IsAuthenticated]
 
class LecturerViewSet(viewsets.ModelViewSet):
  queryset = Lecturer.objects.all()
  serializer_class = LecturerSerializer
  permission_classes = [IsLecturer]

  def get_queryset(self):
    user = self.request.user
    if user.role == 'lecturer':
      # if lecturer_role == 'HoD':
      #   courses = Lecturer.objects.get(user=user).courses
      #   return Lecturer.objects.filter(courses=courses)
      # else:
        return Lecturer.objects.filter(user=user)
    elif user.role =='admin':
      return Lecturer.objects.all()
    else:
      return HttpResponse('You dont have permision to view this')

class ModeViewSet(viewsets.ModelViewSet):
  queryset = Mode.objects.all()
  serializer_class = ModeSerializer
  permission_classes = [IsAuthenticated]

  def get_queryset(self):
    user = self.request.user
    return Mode.objects.all()
  
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
      courses = Lecturer.objects.get(user=user).department.code
      papers = Paper.objects.filter(course_in=courses).count()
      students = Student.objects.filter(course_in=courses).count()
      results = Result.objects.count()
      return response.Response({'courses': courses, 'papers': papers, 'students': students, 'results': results})
    elif user.role == 'admin':
      courses = Course.objects.count()
      papers = Paper.objects.count()
      students = Student.objects.count()
      results = Result.objects.count()
      lecturers = Lecturer.objects.count()
      return response.Response({'courses': courses, 'papers': papers, 'students': students, 'results': results, 'lecturers': lecturers})   

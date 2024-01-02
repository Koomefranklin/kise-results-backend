from os import name
from django.urls import path, re_path

from . import views

urlpatterns = [
  path('', views.IndexPage.as_view(), name='index'),
  path('paperResult/<str:paper>', views.PaperResult.as_view(), name='single_paper'),
  path('student', views.StudentResult.as_view(), name='student_result'),
  path('course/<int:pk>', views.CourseResults.as_view(), name='course_results'),
  re_path(r'^student-autocomplete/$', views.StudentAutocomplete.as_view(), name='student_autocomplete'),
  path('update/<str:pk>', views.StudentPaperUpdate.as_view(), name='result_update'),
]

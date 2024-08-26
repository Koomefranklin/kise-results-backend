from django.urls import path, re_path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'user', views.UserViewSet)
router.register(r'modes', views.ModeViewSet)
router.register(r'course', views.CourseViewSet)
router.register(r'student', views.StudentViewSet)
router.register(r'students', views.StudentListViewSet, basename='student_read_only')
router.register(r'paper', views.PaperViewSet)
router.register(r'module', views.ModuleViewSet)
router.register(r'lecturer', views.LecturerViewSet)
router.register(r'index', views.KnecIndexViewSet)
router.register(r'score', views.ModuleScoreViewSet)
router.register(r'sitting-cat', views.SittingCatViewSet)
router.register(r'result', views.ResultsViewSet)
router.register(r'results', views.ResultsListView, basename='Result_View')
router.register(r'centres', views.CentreViewSet)

app_name = 'dev'

urlpatterns = [
  path('auth/', include('dj_rest_auth.urls')),
  path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
  path('stats/', views.StatisticsView.as_view()),
  path('', include(router.urls)),
]

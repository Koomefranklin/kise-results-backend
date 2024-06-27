from django.urls import path, re_path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'score', views.ScoreViewSet)
router.register(r'user', views.UserViewSet)
router.register(r'student', views.StudentViewSet)
router.register(r'result', views.ResultsViewSet)
router.register(r'course', views.CourseViewSet)
router.register(r'paper', views.PaperViewSet)
router.register(r'specialization', views.SpecializationViewSet)
router.register(r'lecturer', views.LecturerViewSet)
router.register(r'sessions', views.SessionViewSet)
router.register(r'results', views.ResultsListView, basename='Result_View')
router.register(r'index', views.KnecIndexViewSet)

app_name = 'dev'

urlpatterns = [
  path('auth/', include('dj_rest_auth.urls')),
  path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
  path('', include(router.urls)),
]

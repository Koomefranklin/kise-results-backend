"""results URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from dev import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dev.urls')),
    path("__reload__/", include("django_browser_reload.urls")),
    path("accounts/", include('django.contrib.auth.urls')),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('teaching_practice/', include('teaching_practice.urls'), name='teaching_practice')
]
handler403 = 'dev.views.custom_403_view'
handler404 = 'dev.views.custom_404_view'
handler500 = 'dev.views.custom_500_view'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.base_template = 'admin/base_site.html'

from django.urls import path
from . import views

urlpatterns = [
    path('student-autocomplete/', views.StudentAutocomplete.as_view(), name='student-autocomplete'),
    path('', views.IndexPage.as_view(), name='index'),
    path('student-letter/new/', views.NewStudentLetterView.as_view(), name='new_student_letter'),
    path('student/', views.StudentsViewList.as_view(), name='students_tp'),
    path('student-letter/', views.StudentLetterViewList.as_view(), name='student_letters'),
    path('student-letter/<uuid:pk>/edit', views.EditStudentLetterView.as_view(), name='edit_student_letter'),
    path('section/new/', views.NewSectionView.as_view(), name='new_section'),
    path('section/<uuid:pk>/edit/', views.EditsectionView.as_view(), name='edit_section'),
    path('section/', views.SectionViewlist.as_view(), name='sections'),
    path('aspect/new/', views.NewAspectView.as_view(), name='new_aspect'),
    path('aspect/<uuid:pk>/edit/', views.EditAspectView.as_view(), name='edit_aspect'),
    path('aspect/', views.AspectViewList.as_view(), name='aspects'),
    path('student-section/new/', views.NewStudentSectionView.as_view(), name='new_student_section'),
    path('student-section/<uuid:pk>/edit/', views.EditStudentSectionView.as_view(), name='edit_student_section'),
    path('student-section/', views.StudentSectionsViewList.as_view(), name='student_sections'),
    path('student-aspect/new/', views.NewStudentAspectView.as_view(), name='new_student_aspect'),
    path('student-aspect/<uuid:pk>/edit/', views.EditStudentAspectView.as_view(), name='edit_student_aspect'),
    path('student-aspect/', views.StudentAspectsViewList.as_view(), name='student_aspects'),
]
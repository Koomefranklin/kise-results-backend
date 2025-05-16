from django.contrib import admin
from .models import Deadline, Hod, ModuleScore, SitinCat, User, Mode, Lecturer, Student, TeamLeader, Specialization, Paper, Module, CatCombination, Result, IndexNumber, Centre, Course
from teaching_practice import models as tp
from django.contrib.auth.admin import UserAdmin
from .forms import CatCombinationAdminForm, StudentAdminForm, LecturerAdminForm, TeamLeaderAdminForm
# Register your models here.

class CustomUserAdmin(UserAdmin):
  model = User
  search_fields = ['full_name', 'username']
  list_filter = ['is_staff', 'is_active', 'is_superuser', 'role', 'is_first_login']
  
  list_display = [
      'id',
      'full_name',
      'sex',
      'username',
      'is_staff',
      'is_first_login',
  ]
  fieldsets = (
      (
          "Personal Info",
          {
              "fields": (
                  "full_name",
                  "password",
                  "username",
                  "sex",
                  "email",
              )
          },
      ),
      (
          "Permisions",
          {
              "fields": (
                  'role',
                  "is_staff",
                  "is_active",
                  "is_superuser",
                  'is_first_login',
                  "user_permissions",
                  "groups",
              )
          },
      ),
      (
          "Dates",
          {
              "fields": (
                  "date_joined",
                  "last_login",
              )
          },
      ),
  )
  add_fieldsets = (
      (
          None,
          {
              "classes": ("wide",),
              "fields": (
                  "full_name",
                  "sex",
                  "username",
                  "password1",
                  "password2",
                  "is_staff",
                  "is_active",
                  'role',
              ),
          },
      ),
  )

  ordering = ('username',)

class StudentAdmin(admin.ModelAdmin):
  form = StudentAdminForm

class LecturerAdmin(admin.ModelAdmin):
  form = LecturerAdminForm

class TeamLeaderAdmin(admin.ModelAdmin):
  form = TeamLeaderAdminForm

class PaperAdmin(admin.ModelAdmin):
  list_display = ['code', 'name', 'specialization']

class ModuleAdmin(admin.ModelAdmin):
  list_display = ['code', 'name', 'paper']

class ResultAdmin(admin.ModelAdmin):
  list_display = ['student', 'paper', 'cat1', 'cat2']

class CatCombinationAdmin(admin.ModelAdmin):
  add_form = CatCombinationAdminForm 

class TpStudentAdmin(admin.ModelAdmin):
  list_display = ['full_name', 'index', 'created_by']
  search_fields = ['full_name', 'index', 'created_by__full_name']
  # list_filter = ['centre', 'course', 'specialization']

class ModuleScoreAdmin(admin.ModelAdmin):
  list_display = ['student', 'module', 'take_away', 'discussion', 'paper']
  
  def paper(self, obj):
    module = ModuleScore.objects.get(pk=obj.pk).module
    paper = Module.objects.get(pk=module.pk).paper
    return paper
  
class StudentAspectAdmin(admin.ModelAdmin):
  list_display = ['student_section', 'score', 'aspect']
  search_fields = ['aspect__name']


  def aspect(self, obj):
    return obj.aspect.name
  
class St1udentLetterAdmin(admin.ModelAdmin):
  list_display = ['student', 'assessor']
  search_fields = ['pk','student__full_name', 'assessor__full_name']

admin.site.register(User, CustomUserAdmin)
admin.site.register(Mode)
admin.site.register(Lecturer, LecturerAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(TeamLeader, TeamLeaderAdmin)
admin.site.register(Specialization)
admin.site.register(Paper, PaperAdmin)
admin.site.register(Module, ModuleAdmin)
admin.site.register(CatCombination, CatCombinationAdmin)
admin.site.register(Result, ResultAdmin)
admin.site.register(IndexNumber)
admin.site.register(Centre)
admin.site.register(Course)
admin.site.register(ModuleScore, ModuleScoreAdmin)
admin.site.register(SitinCat)
admin.site.register(Deadline)
admin.site.register(Hod)

admin.site.register(tp.Location)
admin.site.register(tp.StudentLetter, St1udentLetterAdmin)
admin.site.register(tp.Section)
admin.site.register(tp.Aspect)
admin.site.register(tp.SubSection)
admin.site.register(tp.Student, TpStudentAdmin)
admin.site.register(tp.StudentAspect, StudentAspectAdmin)

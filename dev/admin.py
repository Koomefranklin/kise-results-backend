from django.contrib import admin
from .models import ModuleScore, User, Session, Lecturer, Student, Specialization, TeamLeader, Course, Paper, Module, CatCombination, LecturerModule, Result, IndexNumber
from django.contrib.auth.admin import UserAdmin
from .forms import CatCombinationAdminForm, StudentAdminForm, LecturerAdminForm, TeamLeaderAdminForm
# Register your models here.

class CustomUserAdmin(UserAdmin):
  model = User
  search_fields = ['full_name', 'username']
  
  list_display = [
      'id',
      'full_name',
      'sex',
      'username',
      'is_staff',
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
  list_display = ['code', 'name', 'course']

class ModuleAdmin(admin.ModelAdmin):
  list_display = ['code', 'name', 'paper']

class ResultAdmin(admin.ModelAdmin):
  list_display = ['student', 'paper', 'cat1', 'cat2']

class CatCombinationAdmin(admin.ModelAdmin):
  add_form = CatCombinationAdminForm 

class ModuleScoreAdmin(admin.ModelAdmin):
  list_display = ['student', 'module', 'score', 'paper']
  
  def paper(self, obj):
    module = ModuleScore.objects.get(pk=obj.pk).module
    paper = Module.objects.get(pk=module.pk).paper
    return paper

admin.site.register(User, CustomUserAdmin)
admin.site.register(Session)
admin.site.register(Lecturer, LecturerAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Specialization)
admin.site.register(TeamLeader, TeamLeaderAdmin)
admin.site.register(Course)
admin.site.register(Paper, PaperAdmin)
admin.site.register(Module, ModuleAdmin)
admin.site.register(CatCombination, CatCombinationAdmin)
admin.site.register(LecturerModule)
admin.site.register(Result, ResultAdmin)
admin.site.register(IndexNumber)
admin.site.register(ModuleScore, ModuleScoreAdmin)

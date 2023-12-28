from django.contrib import admin
from .models import User, Session, Lecturer, Student, Specialization, TeamLeader, Course, Paper, Module, CatCombination, LecturerModule, Result
from django.contrib.auth.admin import UserAdmin
from .forms import StudentAdminForm, LecturerAdminForm, TeamLeaderAdminForm
# Register your models here.

class CustomUserAdmin(UserAdmin):
  model = User
  search_fields = ['surname', 'username', 'other_names']
  
  list_display = [
      'surname',
      'other_names',
      'username',
      'is_staff',
  ]
  fieldsets = (
      (
          "Personal Info",
          {
              "fields": (
                  "username",
                  "password",
                  "surname",
                  "other_names",
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
                  "surname",
                  "other_names",
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

admin.site.register(User, CustomUserAdmin)
admin.site.register(Session)
admin.site.register(Lecturer, LecturerAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Specialization)
admin.site.register(TeamLeader, TeamLeaderAdmin)
admin.site.register(Course)
admin.site.register(Paper)
admin.site.register(Module)
admin.site.register(CatCombination)
admin.site.register(LecturerModule)
admin.site.register(Result)

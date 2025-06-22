from django.contrib import admin

from teaching_practice.forms import AssessmentTypeForm
from teaching_practice.models import Aspect, AssessmentType, Location, Section, Student, StudentAspect, StudentLetter, SubSection

# Register your models here.
class StudentAspectAdmin(admin.ModelAdmin):
  list_display = ['student_section', 'score', 'aspect']
  search_fields = ['aspect__name']


  def aspect(self, obj):
    return obj.aspect.name
  
class StudentLetterAdmin(admin.ModelAdmin):
  list_display = ['student', 'assessor', 'total_score', 'created_at', 'zone']
  search_fields = ['pk','student__full_name', 'assessor__full_name']
  autocomplete_fields = ['student', 'assessor']
  readonly_fields = ['created_at', 'updated_at']
  list_filter = ['assessment_type', 'is_editable', 'to_delete']

class TpStudentAdmin(admin.ModelAdmin):
  list_display = ['full_name', 'index', 'specialization', 'created_by']
  search_fields = ['full_name', 'index', 'created_by__full_name']
  readonly_fields = ['created_at', 'updated_at']
  # list_filter = ['centre', 'course', 'specialization']

class AssessmentTypeAdmin(admin.ModelAdmin):
  list_display = ['course', 'short_name']
  form = AssessmentTypeForm
  filter_horizontal = ('admins',)

admin.site.register(Location)
admin.site.register(StudentLetter, StudentLetterAdmin)
admin.site.register(Section)
admin.site.register(Aspect)
admin.site.register(SubSection)
admin.site.register(Student, TpStudentAdmin)
admin.site.register(StudentAspect, StudentAspectAdmin)
admin.site.register(AssessmentType, AssessmentTypeAdmin)

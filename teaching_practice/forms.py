from django import forms
from dal import autocomplete
from dev.models import User
from .models import Student, Section, StudentAspect, StudentLetter, StudentSection, Aspect

class NewSection(forms.ModelForm):
  class Meta:
    model = Section
    fields = '__all__'

class UpdateSection(forms.ModelForm):
  class Meta:
    model = Section
    fields = '__all__'

class NewAspect(forms.ModelForm):
  class Meta:
    model = Aspect
    fields = '__all__'

class UpdateAspect(forms.ModelForm):
  class Meta:
    model = Aspect
    fields = '__all__'

class NewStudentLetter(forms.ModelForm):
  class Meta:
    model = StudentLetter
    fields = '__all__'

class UpdateStudentLetter(forms.ModelForm):
  class Meta:
    model = StudentLetter
    fields = '__all__'

class NewStudentSection(forms.ModelForm):
  class Meta:
    model = StudentSection
    fields = '__all__'

class UpdateStudentSection(forms.ModelForm):
  class Meta:
    model = StudentSection
    fields = '__all__'

class NewStudentAspect(forms.ModelForm):
  class Meta:
    model = StudentAspect
    fields = '__all__'

class UpdateStudentAspect(forms.ModelForm):
  class Meta:
    model = StudentAspect
    fields = '__all__'
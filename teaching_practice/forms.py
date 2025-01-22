from django import forms
from dal import autocomplete
from dev import views
from dev.models import User
from .models import Location, Student, Section, StudentAspect, StudentLetter, StudentSection, Aspect

class NewSection(forms.ModelForm):
  class Meta:
    model = Section
    fields = ['name', 'contribution']

  def __init__(self, *args, **kwargs):
    super(NewSection, self).__init__(*args, **kwargs)
    for fieldname, field in self.fields.items():
      self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class UpdateSection(forms.ModelForm):
  class Meta:
    model = Section
    fields = '__all__'

  def __init__(self, *args, **kwargs):
    super(UpdateSection, self).__init__(*args, **kwargs)
    for fieldname, field in self.fields.items():
      self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class NewAspect(forms.ModelForm):
  class Meta:
    model = Aspect
    fields = ['section', 'name', 'contribution']
  
  def __init__(self, *args, **kwargs):
    super(NewAspect, self).__init__(*args, **kwargs)
    for fieldname, field in self.fields.items():
      self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class UpdateAspect(forms.ModelForm):
  class Meta:
    model = Aspect
    fields = '__all__'
  
  def __init__(self, *args, **kwargs):
    super(UpdateAspect, self).__init__(*args, **kwargs)
    for fieldname, field in self.fields.items():
      self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class NewStudentForm(forms.ModelForm):
  class Meta:
    model = Student
    fields = ['user', 'department', 'index', 'school', 'grade', 'learning_area']
  
  def __init__(self, *args, **kwargs):
    super(NewStudentForm, self).__init__(*args, **kwargs)
    self.fields['user'].label = 'Student'
    for fieldname, field in self.fields.items():
      self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class StudentForm(forms.ModelForm):
  class Meta:
    model = Student
    fields = ['user', 'department', 'index', 'school', 'grade', 'learning_area']

  def __init__(self, *args, **kwargs):
    super(StudentForm, self).__init__(*args, **kwargs)
    self.fields['user'].label = 'Student'
    for fieldname, field in self.fields.items():
      self.fields[fieldname].disabled = True
      self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class NewLocationForm(forms.Form):
  longitude = forms.FloatField()
  latitude = forms.FloatField()
  
  def __init__(self, *args, **kwargs):
    super(NewLocationForm, self).__init__(*args, **kwargs)
    for fieldname, field in self.fields.items():
      self.fields[fieldname].label = ''
      self.fields[fieldname].widget.attrs['class'] = 'hidden'

class NewStudentLetter(forms.ModelForm):
  class Meta:
    model = StudentLetter
    fields = ['comments']
  
  def __init__(self, *args, **kwargs):
    super(NewStudentLetter, self).__init__(*args, **kwargs)
    for fieldname, field in self.fields.items():
      self.fields[fieldname].label = ''
      self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid hidden'

class UpdateStudentLetter(forms.ModelForm):
  class Meta:
    model = StudentLetter
    fields = ['assessor', 'total_score', 'comments']
  
  def __init__(self, *args, **kwargs):
    super(UpdateStudentLetter, self).__init__(*args, **kwargs)
    self.fields['comments'].widget = forms.Textarea()
    for fieldname, field in self.fields.items():
      if fieldname != 'comments':
        self.fields[fieldname].disabled = True
      self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class NewStudentSection(forms.ModelForm):
  class Meta:
    model = StudentSection
    fields = '__all__'
  
  def __init__(self, *args, **kwargs):
    super(NewStudentSection, self).__init__(*args, **kwargs)
    for fieldname, field in self.fields.items():
      self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class UpdateStudentSection(forms.ModelForm):
  class Meta:
    model = StudentSection
    fields = ['score', 'comments']
  
  def __init__(self, *args, **kwargs):
    super(UpdateStudentSection, self).__init__(*args, **kwargs)
    self.fields['score'].disabled = True
    self.fields['comments'].widget = forms.Textarea()
    for fieldname, field in self.fields.items():
      self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class NewStudentAspect(forms.ModelForm):
  class Meta:
    model = StudentAspect
    fields = '__all__'
  
  def __init__(self, *args, **kwargs):
    super(NewStudentAspect, self).__init__(*args, **kwargs)
    for fieldname, field in self.fields.items():
      self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class UpdateStudentAspect(forms.ModelForm):
  class Meta:
    model = StudentAspect
    fields = '__all__'

  def __init__(self, *args, **kwargs):
    super(UpdateStudentAspect, self).__init__(*args, **kwargs)
    for fieldname, field in self.fields.items():
      self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'
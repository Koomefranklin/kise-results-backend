from dal_gm2m import fields
from django import forms
from dal import autocomplete
from platformdirs import user_cache_path
from dev import views
from dev.models import User
from .models import Location, Student, Section, StudentAspect, StudentLetter, StudentSection, Aspect, SubSection, ZonalLeader

class NewSection(forms.ModelForm):
  class Meta:
    model = Section
    fields = ['number', 'name', 'contribution', 'assessment_type', 'created_by']

  def __init__(self, *args, **kwargs):
    user = kwargs.pop('user', None)
    super(NewSection, self).__init__(*args, **kwargs)
    self.fields['created_by'].initial = user
    self.fields['created_by'].queryset = User.objects.filter(pk=user.pk)
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

class NewSubSection(forms.ModelForm):
  class Meta:
    model = SubSection
    fields = ['section', 'name', 'contribution']

  def __init__(self, *args, **kwargs):
    super(NewSubSection, self).__init__(*args, **kwargs)
    for fieldname, field in self.fields.items():
      self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class UpdateSubSection(forms.ModelForm):
  class Meta:
    model = SubSection
    fields = '__all__'

  def __init__(self, *args, **kwargs):
    super(UpdateSubSection, self).__init__(*args, **kwargs)
    for fieldname, field in self.fields.items():
      self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'


class NewAspect(forms.ModelForm):
  class Meta:
    model = Aspect
    fields = ['section', 'name', 'sub_section', 'contribution', 'created_by']
  
  def __init__(self, *args, **kwargs):
    user = kwargs.pop('user', None)
    super(NewAspect, self).__init__(*args, **kwargs)
    self.fields['created_by'].initial = user
    self.fields['created_by'].queryset = User.objects.filter(pk=user.pk)
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
    fields = ['full_name', 'sex', 'index', 'email']
  
  def __init__(self, *args, **kwargs):
    super(NewStudentForm, self).__init__(*args, **kwargs)
    for fieldname, field in self.fields.items():
      self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid p-2'
    self.fields['full_name'].widget.attrs['class'] = 'rounded border-2 w-5/6 grid p-2'

class StudentForm(forms.ModelForm):
  class Meta:
    model = Student
    fields = ['full_name', 'sex', 'index', 'email']

  def __init__(self, *args, **kwargs):
    super(StudentForm, self).__init__(*args, **kwargs)
    for fieldname, field in self.fields.items():
      self.fields[fieldname].required = True
      self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class NewLocationForm(forms.Form):
  longitude = forms.FloatField()
  latitude = forms.FloatField()
  
  def __init__(self, *args, **kwargs):
    super(NewLocationForm, self).__init__(*args, **kwargs)
    self.fields['latitude'].initial = '-1.2265529324437932'
    self.fields['longitude'].initial = '36.89541538541246'
    for fieldname, field in self.fields.items():
      self.fields[fieldname].label = ''
      self.fields[fieldname].widget.attrs['class'] = 'hidden'

class NewStudentLetter(forms.ModelForm):
  class Meta:
    model = StudentLetter
    fields = ['school', 'grade', 'department', 'learning_area', 'zone', 'late_submission', 'reason']
  
  def __init__(self, *args, **kwargs):
    super(NewStudentLetter, self).__init__(*args, **kwargs)
    self.fields['late_submission'].widget = forms.Select(choices=[(False, 'No'), (True, 'Yes')])
    for fieldname, field in self.fields.items():
      if fieldname != 'late_submission' and fieldname != 'reason':
        self.fields[fieldname].required = True
      self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class UpdateStudentLetter(forms.ModelForm):
  class Meta:
    model = StudentLetter
    fields = ['assessor', 'total_score', 'department', 'school', 'grade', 'learning_area', 'zone', 'late_submission', 'reason', 'location', 'comments']
  
  def __init__(self, *args, **kwargs):
    user = kwargs.pop('user', None)
    super(UpdateStudentLetter, self).__init__(*args, **kwargs)
    # self.fields['late_submission'].widget = forms.Select()
    self.fields['comments'].widget = forms.Textarea()
    self.fields['comments'].label = 'General Comments and Suggestions:'
    self.fields['comments'].required = True
    for fieldname, field in self.fields.items():
      if fieldname != 'comments':
        self.fields[fieldname].disabled = True
      self.fields[fieldname].widget.attrs['class'] = 'p-2 bg-transparent border rounded w-5/6 grid'

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
    self.fields['comments'].label = 'Section Comments'
    self.fields['score'].label = 'Section Score'
    self.fields['score'].widget.attrs['class'] = 'bg-transparent grid'
    self.fields['comments'].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class NewStudentAspect(forms.ModelForm):
  class Meta:
    model = StudentAspect
    fields = '__all__'
  
  def __init__(self, *args, **kwargs):
    super(NewStudentAspect, self).__init__(*args, **kwargs)
    for fieldname, field in self.fields.items():
      self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class UpdateStudentAspect(forms.ModelForm):
  contribution = forms.IntegerField(disabled=True, required=False)
  class Meta:
    model = StudentAspect
    fields = ['aspect', 'score']

  def __init__(self, *args, **kwargs):
    section = kwargs.pop('section', None)
    super(UpdateStudentAspect, self).__init__(*args, **kwargs)
    contribution = self.instance.aspect.contribution
    self.fields['contribution'].initial = contribution
    self.fields['aspect'].disabled = True
    self.fields['aspect'].widget.attrs['class'] = 'p-4 mx-4 bg-transparent w-5/6 grid'
    self.fields['score'].widget.attrs['class'] = 'rounded border-2 grid p-2'
    self.fields['contribution'].widget.attrs['class'] = 'bg-transparent grid p-2'

class ZonalLeaderForm(forms.ModelForm):
  class Meta:
    model = ZonalLeader
    fields = ['zone_name', 'assessor']
    # widgets = {
		# 	'assessor': autocomplete.ModelSelect2(url='lecturer-autocomplete',attrs={
    #     'data-placeholder': 'Search ...',
    #   })
    # }

  def __init__(self, *args, **kwargs):
    super(ZonalLeaderForm, self).__init__(*args, **kwargs)
    self.fields['assessor'].queryset = User.objects.filter(role='lecturer')
    self.fields['assessor'].label = 'Zonal Leader'
    for fieldname, field in self.fields.items():
      self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 p-2 m2 grid'
      
StudentAspectFormSet = forms.modelformset_factory(
  StudentAspect,
  UpdateStudentAspect,
  extra=0
)

class SearchForm(forms.Form):
	search_query = forms.CharField(label='Search', widget=forms.TextInput(attrs={'placeholder': 'Input Search Query'}))
	
	def __init__(self, *args, **kwargs):
		super(SearchForm, self).__init__(*args, **kwargs)
		self.fields['search_query'].widget.attrs['class'] = 'w-full h-fit p-2'

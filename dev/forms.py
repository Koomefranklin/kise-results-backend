from dataclasses import fields
import datetime
from django import forms
from .models import CatCombination, Deadline, Hod, Specialization, Module, Paper, User, Lecturer, Student, TeamLeader, Result, IndexNumber, ModuleScore, SitinCat
from dal import autocomplete
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, SetPasswordForm, PasswordChangeForm, AdminPasswordChangeForm
from django.utils import timezone

class StudentAdminForm(forms.ModelForm):
	class Meta:
		model = Student
		fields = '__all__'

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['user'].queryset = User.objects.filter(role='student')

class LecturerAdminForm(forms.ModelForm):
	class Meta:
		model = Lecturer
		fields = '__all__'

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['user'].queryset = User.objects.filter(role='lecturer')

class TeamLeaderAdminForm(forms.ModelForm):
	class Meta:
		model = TeamLeader
		fields = '__all__'

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['lecturer'].queryset = Lecturer.objects.filter(role='TL')

class CatCombinationAdminForm(forms.ModelForm):
	class Meta:
		model = CatCombination
		fields = '__all__'

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['cat1'].queryset = Module.objects.filter(Q(cat1__isnull=True) & Q(cat2__isnull=True))
		self.fields['cat2'].queryset = Module.objects.filter(Q(cat1__isnull=True) & Q(cat2__isnull=True))
		self.fields['paper'].queryset = Paper.objects.filter(catcombination__isnull=True)

class StudentPaperUpdateForm(forms.ModelForm):
	class Meta:
		model = Result
		fields = '__all__'

	def __init__(self, *args, **kwargs):
		super(StudentPaperUpdateForm, self).__init__(*args, **kwargs)
		self.fields['student'].disabled = True
		self.fields['paper'].disabled = True

class AdmissionNumberForm(forms.ModelForm):
	class Meta:
		model = IndexNumber
		fields = ['student', 'index']
	
class CustomUserCreationForm(UserCreationForm):
	class Meta:
		model = User
		fields = ('full_name', 'username', 'password1', 'password2', 'sex')

	def __init__(self, *args, **kwargs):
		user = kwargs.pop('user', None)
		super(CustomUserCreationForm, self).__init__(*args, **kwargs)
		# for fieldname in ['username', 'password1', 'password2']:
		#   self.fields[fieldname].help_text = None

		# Adding extra class in the html tags
		for fieldname, field in self.fields.items():
			self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

	def save(self, commit=True):
		instance = super().save(commit=False)
		cleaned = self.cleaned_data
		role = cleaned.get('role')
		if role == 'admin':
			instance.is_staff = True
		if commit:
			instance.save()
		return instance

class CustomUserChangeForm(UserChangeForm):
  password = None
  class Meta:
    model = User
    fields = ['full_name', 'role', 'sex']

  def __init__(self, *args, **kwargs):
    user = kwargs.pop('user', None)
    super(CustomUserChangeForm, self).__init__(*args, **kwargs)

    # Adding extra class in the html tags
    for fieldname, field in self.fields.items():
      self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class CustomPasswordChangeForm(PasswordChangeForm):

  def __init__(self, *args, **kwargs):
    super(CustomPasswordChangeForm, self).__init__( *args, **kwargs)

    # Adding extra class in the html tags
    for fieldname, field in self.fields.items():
      self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class NewStudent(forms.ModelForm):
	class Meta:
		model = Student
		fields = ['admission', 'specialization', 'mode', 'centre', 'year']

	def __init__(self, *args, **kwargs):
		user = kwargs.pop('user', None)
		super(NewStudent, self).__init__(*args, **kwargs)
		self.fields['year'].widget = forms.DateInput()
    # Adding extra class in the html tags
		for fieldname, field in self.fields.items():
			self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class UpdateStudent(forms.ModelForm):
	class Meta:
		model = Student
		fields = '__all__'
	
	def __init__(self, *args, **kwargs):
		super(UpdateStudent, self).__init__(*args, **kwargs)
		for fieldname, field in self.fields.items():
			self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'
	
class NewLecturer(forms.ModelForm):
	class Meta:
		model = Lecturer
		fields = ['specializations']
		widgets = {'specializations': forms.CheckboxSelectMultiple()}

		def __init__(self, *args, **kwargs):
			user = kwargs.pop('user', None)
			super(NewLecturer, self).__init__(*args, **kwargs)
			# Adding extra class in the html tags
			for fieldname, field in self.fields.items():
				self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class UpdateLecturer(forms.ModelForm):
	class Meta:
		model = Lecturer
		fields = ['user', 'specializations']
		widgets = {'specializations': forms.CheckboxSelectMultiple()}

		def __init__(self, *args, **kwargs):
			user = kwargs.pop('user', None)
			super(UpdateLecturer, self).__init__(*args, **kwargs)
			self.fields['user'].disabled = True
			# Adding extra class in the html tags
			for fieldname, field in self.fields.items():
				self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class NewHoD(forms.ModelForm):
	class Meta:
		model = Hod
		fields = ['lecturer', 'department']

		def __init__(self, *args, **kwargs):
			user = kwargs.pop('user', None)
			super(NewHoD, self).__init__(*args, **kwargs)
			# Adding extra class in the html tags
			for fieldname, field in self.fields.items():
				self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class UpdateHoD(forms.ModelForm):
	class Meta:
		model = Hod
		fields = ['lecturer', 'department']

		def __init__(self, *args, **kwargs):
			user = kwargs.pop('user', None)
			super(UpdateHoD, self).__init__(*args, **kwargs)
			# Adding extra class in the html tags
			for fieldname, field in self.fields.items():
				self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class NewTeamLeader(forms.ModelForm):
	class Meta:
		model = TeamLeader
		fields = ['centre', 'lecturer']

		def __init__(self, *args, **kwargs):
			user = kwargs.pop('user', None)
			super(NewTeamLeader, self).__init__(*args, **kwargs)
			# Adding extra class in the html tags
			for fieldname, field in self.fields.items():
				self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class UpdateTeamLeader(forms.ModelForm):
	class Meta:
		model = TeamLeader
		fields = ['centre', 'lecturer']

		def __init__(self, *args, **kwargs):
			user = kwargs.pop('user', None)
			super(UpdateTeamLeader, self).__init__(*args, **kwargs)
			# Adding extra class in the html tags
			for fieldname, field in self.fields.items():
				self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class NewSpecialization(forms.ModelForm):
	class Meta:
		model = Specialization
		fields = '__all__'
	
	def __init__(self, *args, **kwargs):
		super(NewSpecialization, self).__init__(*args, **kwargs)
		for fieldname, field in self.fields.items():
			self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class UpdateSpecialization(forms.ModelForm):
	class Meta:
		model = Specialization
		fields = '__all__'
	
	def __init__(self, *args, **kwargs):
		super(UpdateSpecialization, self).__init__(*args, **kwargs)
		for fieldname, field in self.fields.items():
			self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class NewPaper(forms.ModelForm):
	class Meta:
		model = Paper
		fields = '__all__'
	
	def __init__(self, *args, **kwargs):
		super(NewPaper, self).__init__(*args, **kwargs)
		for fieldname, field in self.fields.items():
			self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'
	
class UpdatePaper(forms.ModelForm):
	class Meta:
		model = Paper
		fields = '__all__'
	
	def __init__(self, *args, **kwargs):
		super(UpdatePaper, self).__init__(*args, **kwargs)
		for fieldname, field in self.fields.items():
			self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'
	
class NewModule(forms.ModelForm):
	class Meta:
		model = Module
		fields = '__all__'
	
	def __init__(self, *args, **kwargs):
		super(NewModule, self).__init__(*args, **kwargs)
		for fieldname, field in self.fields.items():
			self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class UpdateModule(forms.ModelForm):
	class Meta:
		model = Module
		fields = '__all__'

	def __init__(self, *args, **kwargs):
		super(UpdateModule, self).__init__(*args, **kwargs)
		for fieldname, field in self.fields.items():
			self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'
	

class NewModuleScore(forms.ModelForm):
	class Meta:
		model = ModuleScore
		fields = ['student', 'module', 'discussion', 'take_away']
		widgets = {
					'student': autocomplete.ModelSelect2(url='student-autocomplete',attrs={
        'data-placeholder': 'Search ...'
    },)
        }
	def __init__(self, *args, **kwargs):
		user = kwargs.pop('user', None)
		paper = kwargs.pop('paper', None)
		takeaway_deadline = Deadline.objects.get(name='takeaway').deadline
		discussion_deadline = Deadline.objects.get(name='discussion').deadline
		super(NewModuleScore, self).__init__(*args, **kwargs)

		specialization = Paper.objects.get(pk=paper).specialization

		self.fields['student'].queryset = Student.objects.filter(specialization=specialization)
		self.fields['module'].queryset = Module.objects.filter(paper=paper)

		if timezone.now() < takeaway_deadline:
			self.fields['take_away'].disabled = True
			self.fields['take_away'].help_text = f'Deadline was on {timezone.localtime(takeaway_deadline)}'
		if timezone.now() < discussion_deadline:
			self.fields['discussion'].disabled = True
			self.fields['discussion'].help_text = f'Deadline was on {timezone.localtime(discussion_deadline)}'

    # Adding extra class in the html tags
		for fieldname, field in self.fields.items():
			self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class UpdateModuleScore(forms.ModelForm):
	class Meta:
		model = ModuleScore
		fields = ['student', 'module', 'discussion', 'take_away', 'added_by', 'updated_by']

	def __init__(self, *args, **kwargs):
		user = kwargs.pop('user', None)
		takeaway_deadline = Deadline.objects.get(name='takeaway').deadline
		discussion_deadline = Deadline.objects.get(name='discussion').deadline
		super(UpdateModuleScore, self).__init__(*args, **kwargs)
		
		if timezone.now() < takeaway_deadline:
			self.fields['take_away'].disabled = True
			self.fields['take_away'].help_text = f'Deadline was on {timezone.localtime(takeaway_deadline)}'
		if timezone.now() < discussion_deadline:
			self.fields['discussion'].disabled = True
			self.fields['discussion'].help_text = f'Deadline was on {timezone.localtime(discussion_deadline)}'

		for fieldname, field in self.fields.items():
			self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'
			if fieldname not in ['discussion', 'take_away']:
				self.fields[fieldname].disabled = True

class NewSitinCat(forms.ModelForm):
	class Meta:
		model = SitinCat
		fields = ['student','paper', 'cat1', 'cat2']
		widgets = {
					'student': autocomplete.ModelSelect2(url='student-autocomplete',attrs={
        'data-placeholder': 'Search ...',
    },)
        }
	def __init__(self, *args, **kwargs):
		user = kwargs.pop('user', None)
		paper = kwargs.pop('paper', None)
		cat1_deadline = Deadline.objects.get(name='cat1').deadline
		cat2_deadline = Deadline.objects.get(name='cat2').deadline
		super(NewSitinCat, self).__init__(*args, **kwargs)
		specialization = Paper.objects.get(pk=paper).specialization

		self.fields['student'].queryset = Student.objects.filter(specialization=specialization)
		
		self.fields['paper'].initial = Paper.objects.get(pk=paper)
		self.fields['paper'].queryset = Paper.objects.filter(pk=paper)

    # Adding extra class in the html tags
		for fieldname, field in self.fields.items():
			self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class UpdateSitinCat(forms.ModelForm):
	class Meta:
		model = SitinCat
		fields = '__all__'
	
	def __init__(self, *args, **kwargs):
		cat1_deadline = Deadline.objects.get(name='cat1').deadline
		cat2_deadline = Deadline.objects.get(name='cat2').deadline
		super(UpdateSitinCat, self).__init__(*args, **kwargs)
		for fieldname, field in self.fields.items():
			self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'
			if fieldname not in ['cat1', 'cat2']:
				self.fields[fieldname].disabled = True

class NewDeadline(forms.ModelForm):
	date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="Date")
	time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), label="Time")

	class Meta:
		model = Deadline
		fields = ['name', 'date', 'time']
	
	def __init__(self, *args, **kwargs):
		super(NewDeadline, self).__init__(*args, **kwargs)
		for fieldname, field in self.fields.items():
			self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

	def clean(self):
		cleaned_data = super().clean()
		date = cleaned_data.get('date')
		time = cleaned_data.get('time')

		if date and time:
			cleaned_data['deadline'] = datetime.datetime.combine(date, time)

		return cleaned_data

class UpdateDeadline(forms.ModelForm):
	# date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="Date")
	# time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), label="Time")

	class Meta:
		model = Deadline
		fields = ['name', 'deadline']
	
	def __init__(self, *args, **kwargs):
		super(UpdateDeadline, self).__init__(*args, **kwargs)
		self.fields['name'].disabled = True
		for fieldname, field in self.fields.items():
			self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'
	
class NewCatCombination(forms.ModelForm):
	class Meta:
		model = CatCombination
		fields = ['paper', 'cat1', 'cat2']
		widgets = {
			'cat1': forms.CheckboxSelectMultiple(),
			'cat2': forms.CheckboxSelectMultiple()
		}
	
	def __init__(self, *args, **kwargs):
		super(NewCatCombination, self).__init__(*args, **kwargs)
		for fieldname, field in self.fields.items():
			self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'

class UpdateCatCombination(forms.ModelForm):
	class Meta:
		model = CatCombination
		fields = ['paper', 'cat1', 'cat2']
		widgets = {
			'cat1': forms.CheckboxSelectMultiple(),
			'cat2': forms.CheckboxSelectMultiple()
		}
	
	def __init__(self, *args, **kwargs):
		super(UpdateCatCombination, self).__init__(*args, **kwargs)
		self.fields['paper'].disabled = True
		for fieldname, field in self.fields.items():
			self.fields[fieldname].widget.attrs['class'] = 'rounded border-2 w-5/6 grid'
	
class CSVUploadForm(forms.Form):
	csv_file = forms.FileField(label='Select a CSV file containing the details')

from django import forms
from .models import User, Lecturer, Student, TeamLeader

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

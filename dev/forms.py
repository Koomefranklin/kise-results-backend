from django import forms
from .models import Paper, User, Lecturer, Student, TeamLeader, Result
from dal import autocomplete

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

class ResultForm(forms.ModelForm):
	class Meta:        
		model = Result
		fields = ['student', 'cat1', 'cat2', 'session', 'paper']

		widgets = {
			'student': autocomplete.ModelSelect2(url='student_autocomplete')
		}
				
	def __init__(self, request, *args, **kwargs):
		super(ResultForm, self).__init__(*args, **kwargs)
		user = request.request.user
		self.fields['paper'].widget = forms.TextInput()
		self.fields['paper'].initial = Paper.objects.get(pk=request.kwargs.get('paper'))
		self.fields['paper'].disabled = True

class StudentPaperUpdateForm(forms.ModelForm):
	class Meta:
		model = Result
		fields = '__all__'

	def __init__(self, *args, **kwargs):
		super(StudentPaperUpdateForm, self).__init__(*args, **kwargs)
		self.fields['student'].disabled = True
		self.fields['paper'].disabled = True

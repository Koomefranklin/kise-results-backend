from django import forms
from .models import CatCombination, Module, Paper, User, Lecturer, Student, TeamLeader, Result, KnecIndexNumber, ModuleScore
# from dal import autocomplete
from django.db.models import Q

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

# class ScoreForm(forms.ModelForm):
# 	class Meta:        
# 		model = ModuleScore
# 		fields = ['student', 'module', 'score']

# 		widgets = {
# 			'student': autocomplete.ModelSelect2(url='student_autocomplete'),
# 			'module': autocomplete.ModelSelect2(url='module_autocomplete')
# 		}

# 		def __init__(self, *args, **kwargs):
# 			super(ScoreForm, self).__init__(*args, **kwargs)

class StudentPaperUpdateForm(forms.ModelForm):
	class Meta:
		model = Result
		fields = '__all__'

	def __init__(self, *args, **kwargs):
		super(StudentPaperUpdateForm, self).__init__(*args, **kwargs)
		self.fields['student'].disabled = True
		self.fields['paper'].disabled = True

class KnecIndexForm(forms.ModelForm):
	class Meta:
		model = KnecIndexNumber
		fields = ['student', 'index']

from django.shortcuts import render
from dal import autocomplete
from django.urls import reverse_lazy
from dev.models import User
from teaching_practice.forms import NewAspect, NewSection, NewStudentAspect, NewStudentLetter, NewStudentSection, UpdateAspect, UpdateSection, UpdateStudentAspect, UpdateStudentLetter, UpdateStudentSection
from .models import Student, Section, StudentAspect, StudentLetter, StudentSection, Aspect
from django.views.generic import ListView, CreateView, FormView, UpdateView
from django.db.models import Q, Avg, F, ExpressionWrapper, FloatField, Value
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.

class StudentAutocomplete(autocomplete.Select2QuerySetView):
	def get_queryset(self):
		user = self.request.user
		qs = Student.objects.filter(user__is_active=True)
		if self.q:
			qs = qs.filter(Q(user__full_name__icontains=self.q) | Q(index_icontains=self.q))
		return qs

class IndexPage(LoginRequiredMixin, ListView):
	model = User
	template_name = 'teachingPractice/index.html'
	context_object_name = 'dashboard'

	def get_queryset(self):
		return User.objects.filter(pk=self.request.user.pk)
	
	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		return context

class NewSectionView(LoginRequiredMixin, CreateView):
	model = Section
	form_class = NewSection
	template_name = 'teaching_practice/base_form.html'
	success_url = reverse_lazy('sections')
	
	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		return context

class EditsectionView(LoginRequiredMixin, UpdateView):
	model = Section
	form_class = UpdateSection
	template_name = 'teaching_practice/base_form.html'
	success_url = reverse_lazy('sections')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		return context
	

class SectionViewlist(LoginRequiredMixin, ListView):
	model = Section
	template_name = 'teaching_practice/sections.html'
	context_object_name = 'sections'
	paginate_by = 20
	
	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		return context

class NewAspecView(LoginRequiredMixin, CreateView):
	model = Aspect
	form_class = NewAspect
	template_name = 'teaching_practice/base_form.html'
	success_url = reverse_lazy('aspects')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		return context

class EditAspectView(LoginRequiredMixin, UpdateView):
	model = Aspect
	form_class = UpdateAspect
	template_name = 'teaching_practice/base_form.html'
	success_url = reverse_lazy('aspects')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		return context

class AspectViewList(LoginRequiredMixin, ListView):
	model = Aspect
	template_name = 'teaching_practice/aspects.html'
	context_object_name = 'aspects'
	paginate_by = 20

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		return context

class StudentsViewList(LoginRequiredMixin, ListView):
	model = Student
	template_name = 'teaching_practice/students.html'
	context_object_name = 'students'
	paginate_by = 20

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		return context

class NewStudentLetterView(LoginRequiredMixin, FormView):
	model = StudentLetter
	form_class = NewStudentLetter
	template_name = 'teaching_practice/base_form.html'
	success_url = reverse_lazy('studentletters')
	
	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		return context

class EditStudentLetterView(LoginRequiredMixin, UpdateView):
	model = StudentLetter
	form_class = UpdateStudentLetter
	template_name = 'teaching_practice/base_form.html'
	success_url = reverse_lazy('studentletters')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		return context

class StudentLetterViewList(LoginRequiredMixin, ListView):
	model = StudentLetter
	template_name = 'teaching_practice/student_letters.html'
	context_object_name = 'studentletters'
	paginate_by = 20

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		return context

class NewStudentSectionView(LoginRequiredMixin, CreateView):
	model = StudentSection
	form_class = NewStudentSection
	template_name = 'teaching_practice/base_form.html'
	success_url = reverse_lazy('studentsections')
	
	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		return context

class EditStudentSection(LoginRequiredMixin, UpdateView):
	model = StudentSection
	form_class = UpdateStudentSection
	template_name = 'teaching_practice/base_form.html'
	success_url = reverse_lazy('studentsections')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		return context

class StudentSectionsViewList(LoginRequiredMixin, ListView):
	model = StudentSection
	template_name = 'teaching_practice/student_sections.html'
	context_object_name = 'studentsections'
	paginate_by = 20

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		return context

class NewStudentAspectView(LoginRequiredMixin, CreateView):
	model = StudentAspect
	form_class = NewStudentAspect
	template_name = 'teaching_practice/base_form.html'
	success_url = reverse_lazy('studentaspects')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		return context

class EditStudentAspectView(LoginRequiredMixin, UpdateView):
	model = StudentAspect
	form_class = UpdateStudentAspect
	template_name = 'teaching_practice/base_form.html'
	success_url = reverse_lazy('studentaspects')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		return context

class StudentAspectsViewList(LoginRequiredMixin, ListView):
	model = StudentAspect
	template_name = 'teaching_practice/student_aspects.html'
	context_object_name = 'studentaspects'
	paginate_by = 20

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		return context

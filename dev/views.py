from typing import Any
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.views.generic import ListView, CreateView, FormView, UpdateView
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin

from .mixins import AdminMixin, AdminOrHeadMixin, AdminOrLecturerMixin
from .models import Deadline, Hod, ModuleScore, User, Student, Result, Mode, Lecturer, Specialization, Paper, TeamLeader, Module, CatCombination, IndexNumber, SitinCat, Centre
from django.http.response import HttpResponse
from .forms import CSVUploadForm, CustomPasswordChangeForm, CustomUserCreationForm, CustomUserChangeForm, NewCatCombination, NewDeadline, NewHoD, NewStudent, NewTeamLeader, UpdateCatCombination, UpdateDeadline, UpdateHoD, UpdateStudent, NewLecturer, UpdateLecturer, NewSpecialization, UpdateSpecialization, NewPaper, UpdatePaper, NewModule, UpdateModule, NewModuleScore, UpdateModuleScore, NewSitinCat, UpdateSitinCat, UpdateTeamLeader
from itertools import chain
from dal import autocomplete
from django.urls import reverse_lazy
from django.contrib import messages
import csv

# Create your views here.

class StudentAutocomplete(autocomplete.Select2QuerySetView):
	def get_queryset(self):
		user = self.request.user
		paper = self.forwarded.get('paper', None)
		print(self.forwarded)
		# if user.role == 'admin':
		# 	qs = None
		# elif user.role == 'lecturer':
		specializations = Lecturer.objects.get(user=user).specializations.values_list('id', flat=True)
		qs = Student.objects.filter(specialization__in=specializations)
		if self.q:
			qs = qs.filter(Q(user__full_name__icontains=self.q) | Q(admission__icontains=self.q))
		if paper:
			specialization = Paper.objects.get(pk=paper).specialization
			qs = qs.filter(specialization=specialization)
		return qs

class ModuleAutocomplete(autocomplete.Select2QuerySetView):
	def get_queryset(self):
		user = self.request.user
		if user.role == 'admin':
			qs = Module.objects.all()
		elif user.role == 'lecturer':
			specializations = Lecturer.objects.filter(user=user).values_list('id', flat=True)
			papers = Paper.objects.filter(specialization__in=specializations)
			qs = Module.objects.filter(paper__in= papers)
		if self.q:
			qs = qs.filter(Q(paper__icontains=self.q) | Q(admission__icontains=self.q))
		return qs

class Index(LoginRequiredMixin, ListView):
	model = User
	template_name = 'results/index.html'
	context_object_name = 'dashboard'

	def get_queryset(self):
		return User.objects.filter(pk=self.request.user.pk)

	def get_context_data(self, **kwargs):
		user = self.request.user
		deadlines = Deadline.objects.all()
		if user.role == 'admin':
			students = Student.objects.all().count()
			lecturers = Lecturer.objects.all().count()
			specializations = Specialization.objects.all().count()
			papers = Paper.objects.all().count()
			modules = Module.objects.all().count()

		elif user.role == 'lecturer':
			lecturer = Lecturer.objects.get(user=user)
			dl = Mode.objects.filter(Q(mode='DL') | Q(mode='Common')).values_list('id')
			ft = Mode.objects.filter(Q(mode='FT') | Q(mode='Common')).values_list('id')
			hods = Hod.objects.all().values_list('lecturer', flat=True)
			tls = TeamLeader.objects.all().values_list('lecturer', flat=True)
			if lecturer in tls:
				tl = TeamLeader.objects.get(lecturer=lecturer)
				students = Student.objects.filter(center=tl.center).count()
				lecturers = Lecturer.objects.filter().count()
				all_specializations = Specialization.objects.filter(mode__in=dl).values_list('id', flat=True)
				all_papers = Paper.objects.filter(specialization__in=all_specializations).values_list('id')
				modules = Module.objects.filter(paper__in=all_papers).count()
				specializations = all_specializations.count()
				papers = all_papers.count()
			elif lecturer in hods:
				hod = Hod.objects.get(lecturer=lecturer)
				students = Student.objects.filter(specialization=hod.specialization).count()
				lecturers = Lecturer.objects.filter().count()
				all_specializations = lecturer.specializations
				all_papers = Paper.objects.filter(specialization__in=all_specializations).values_list('id')
				modules = Module.objects.filter(paper__in=all_papers).count()
				specializations = all_specializations.count()
				papers = all_papers.count()
			else:
				all_specializations = lecturer.specializations.values_list('id', flat=True)
				students = Student.objects.filter(specialization__in=all_specializations).count()
				lecturers = Lecturer.objects.filter().count()
				papers = Paper.objects.filter(specialization__in=all_specializations).values_list('id', flat=True)
				modules = Module.objects.filter(paper__in=papers).count()
				specializations = all_specializations.count()
				papers = papers.count()
		elif user.role == 'student':
			pass
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['students'] = students
		context['lecturers'] = lecturers
		context['specializations'] = specializations
		context['papers'] = papers
		context['modules'] = modules
		context['title'] = 'Dashboard'
		context['center'] = 'KISE'
		context['deadlines'] = deadlines
		return context

class UpdateUserPassword(LoginRequiredMixin, FormView):
	form_class = CustomPasswordChangeForm
	template_name = 'registration/change_password.html'
	success_url = reverse_lazy('dashboard')

	def get_form_kwargs(self):
		kwargs = super(UpdateUserPassword, self).get_form_kwargs()
		kwargs['user'] = self.request.user
		return kwargs
	
	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['title'] = 'Password Change'
		context['is_nav_enabled'] = True
		return context

class StudentsViewList(LoginRequiredMixin, ListView):
	model = Student
	template_name = 'results/students.html'
	context_object_name = 'students'
	paginate_by = 50

	def get_queryset(self):
		user = self.request.user
		if user.role == 'admin':
			qs = Student.objects.all()
		elif user.role == 'lecturer':
			specializations = Lecturer.objects.get(user=user).specializations.values_list('id', flat=True)
			qs = Student.objects.filter(specialization__in=specializations)
		return qs

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Students'
		return context
	pass

class StudentCreateView(LoginRequiredMixin, AdminMixin, FormView):
	model = Student
	form_class = CustomUserCreationForm
	template_name = 'results/new_student.html'
	success_url = reverse_lazy('students')

	def get_context_data(self, **kwargs):
		user = self.request.user

		if user.role == 'admin':
			pass
		elif user.role == 'lecturer':
			lecturer = Lecturer.objects.get(user=user)
			if lecturer.role == 'TL' or lecturer.role == 'hod':
				pass
			else:
				pass
		elif user.role == 'student':
			pass
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		if 'student_form' not in context:
			context['student_form'] = NewStudent()
		context['title'] = 'New Student'
		return context

	def post(self, request, *args, **kwargs):
				user_form = self.get_form(self.get_form_class())
				student_form = NewStudent(self.request.POST)

				if user_form.is_valid() and student_form.is_valid():
						user_instance = user_form.save()

						student = student_form.save(commit=False)
						student.user = user_instance
						student.added_by = self.request.user
						student.save()
						messages.success(self.request, f'Added {student.admission} Successfully')

						return redirect(self.get_success_url())

				return self.form_invalid(user_form, student_form)

	def form_invalid(self, user_form, book_form):
			"""
			Renders the forms again with errors when validation fails.
			"""
			context = self.get_context_data()
			context['user_form'] = user_form
			context['student_form'] = book_form
			return self.render_to_response(context)

class StudentUpdateView(LoginRequiredMixin, AdminMixin, UpdateView):
	model = Student
	form_class = UpdateStudent
	template_name = 'results/base_form.html'
	success_url = reverse_lazy('students')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		if user.role == 'admin':
			pass
		elif user.role == 'lecturer':
			lecturer = Lecturer.objects.get(user=user)
			if lecturer.role == 'TL' or lecturer.role == 'hod':
				pass
			else:
				pass
		elif user.role == 'student':
			pass
		return context
	pass

class LecturersListView(LoginRequiredMixin, ListView):
	model = Lecturer
	template_name = 'results/lecturers.html'
	context_object_name = 'lecturers'
	paginate_by = 50

	def get_queryset(self):
		user = self.request.user
		query = self.request.GET.get('query')
		if user.role == 'admin':
			qs = Lecturer.objects.all()
		elif user.role == 'lecturer':
			lecturer = Lecturer.objects.get(user=user).id
			hods = Hod.objects.all()
			if lecturer in hods.values_list('lecturer', flat=True):
				department = hods.get(lecturer=lecturer).department.id
				qs = Lecturer.objects.filter(specializations__id=department)
			else:
				qs = Lecturer.objects.filter(user=user)
		if query:
			qs = qs.filter(user__full_name__icontains=query)
		return qs

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Lecturers'
		return context
	pass

class LecturerCreateView(LoginRequiredMixin, AdminMixin, FormView):
	model = Lecturer
	form_class = CustomUserCreationForm
	template_name = 'results/new_lecturer.html'
	success_url = reverse_lazy('lecturers')

	def get_context_data(self, **kwargs):
		user = self.request.user

		if user.role == 'admin':
			pass
		elif user.role == 'lecturer':
			lecturer = Lecturer.objects.get(user=user)
			if lecturer.role == 'TL' or lecturer.role == 'hod':
				pass
			else:
				pass
		elif user.role == 'student':
			pass
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'New Lecturer'
		if 'lecturer_form' not in context:
			context['lecturer_form'] = NewLecturer()
		return context

	def post(self, request, *args, **kwargs):
		user_form = self.get_form(self.get_form_class())
		lecturer_form = NewLecturer(self.request.POST)

		if user_form.is_valid() and lecturer_form.is_valid():
			user_instance = user_form.save(commit=False)
			user_instance.role = 'lecturer'
			user_instance.save()
			lecturer = lecturer_form.save(commit=False)
			lecturer.user = user_instance
			lecturer.added_by = self.request.user
			lecturer.save()

			messages.success(self.request, f'Added {lecturer.user.full_name} Successfully')

			return redirect(self.get_success_url())

		return self.form_invalid(user_form, lecturer_form)

	def form_invalid(self, user_form, lecturer_form):
		"""
		Renders the forms again with errors when validation fails.
		"""
		context = self.get_context_data()
		context['user_form'] = user_form
		context['lecturer_form'] = lecturer_form
		return self.render_to_response(context)

class LecturerUpdateView(LoginRequiredMixin, AdminOrHeadMixin, UpdateView):
	model = Lecturer
	form_class = UpdateLecturer
	template_name = 'results/new_lecturer.html'
	success_url = reverse_lazy('lecturers')

	def get_context_data(self, **kwargs):
		user = self.request.user

		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Update Lecturer'
		# if 'lecturer_form' not in context:
		# 	context['lecturer_form'] = UpdateLecturer()
		return context

	def form_valid(self, form):
		form.instance.updated_by = self.request.user
		return super().form_valid(form)
	
	# def post(self, request, *args, **kwargs):
	# 	lecturer_id = self.kwargs.get('pk')
	# 	user_form = self.get_form(self.get_form_class())
	# 	lecturer_form = UpdateLecturer(self.request.POST)

	# 	if user_form.is_valid() and lecturer_form.is_valid():
	# 		user_instance = user_form.save()
	# 		lecturer = lecturer_form.save(commit=False)
	# 		lecturer.user = user_instance
	# 		lecturer.updated_by = self.request.user
	# 		lecturer.save()

	# 		messages.success(self.request, f'Updated {lecturer.user.full_name} Successfully')

	# 		return redirect(self.get_success_url())

	# 	return self.form_invalid(user_form, lecturer_form)

	# def form_invalid(self, user_form, lecturer_form):
	# 		"""
	# 		Renders the forms again with errors when validation fails.
	# 		"""
	# 		context = self.get_context_data()
	# 		context['user_form'] = user_form
	# 		context['lecturer_form'] = lecturer_form
	# 		return self.render_to_response(context)

class SpecializationsViewList(LoginRequiredMixin, ListView):
	model = Specialization
	template_name = 'results/specializations.html'
	context_object_name = 'specializations'
	paginate_by = 20

	def get_queryset(self):
		user = self.request.user
		if user.role == 'admin':
			qs = Specialization.objects.all()
		elif user.role == 'lecturer':
			specializations = Lecturer.objects.get(user=user).specializations.values_list('id', flat=True)
			qs = Specialization.objects.filter(pk__in=specializations)
		return qs.order_by('code')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Specializations'
		return context

class SpecializationCreateView(LoginRequiredMixin, AdminMixin, CreateView):
	model = Specialization
	form_class = NewSpecialization
	template_name = 'results/base_form.html'
	success_url = reverse_lazy('specializations')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		if user.role == 'admin':
			pass
		elif user.role == 'lecturer':
			lecturer = Lecturer.objects.get(user=user)
			if lecturer.role == 'TL' or lecturer.role == 'hod':
				pass
			else:
				pass
		elif user.role == 'student':
			pass
		return context
	pass

class SpecializationUpdateView(LoginRequiredMixin, AdminMixin, UpdateView):
	model = Specialization
	form_class = UpdateSpecialization
	template_name = 'results/base_form.html'
	success_url = reverse_lazy('specializations')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		if user.role == 'admin':
			pass
		elif user.role == 'lecturer':
			lecturer = Lecturer.objects.get(user=user)
			if lecturer.role == 'TL' or lecturer.role == 'hod':
				pass
			else:
				pass
		elif user.role == 'student':
			pass
		return context
	pass

class PapersViewList(LoginRequiredMixin, ListView):
	model = Paper
	template_name = 'results/papers.html'
	context_object_name = 'papers'
	paginate_by = 20

	def get_queryset(self):
		user = self.request.user
		specialization = self.request.GET.get('sp')
		print(specialization)
		if user.role == 'admin':
			qs = Paper.objects.all().order_by('code')
		elif user.role == 'lecturer':
			specializations = Lecturer.objects.get(user=user).specializations.values_list('id', flat=True)
			qs = Paper.objects.filter(specialization__in=specializations)
		if specialization:
			qs = qs.filter(specialization=specialization)
		return qs.order_by('code')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Papers'
		return context

class PaperCreateView(LoginRequiredMixin, AdminMixin, CreateView):
	model = Paper
	form_class = NewPaper
	template_name = 'results/base_form.html'
	success_url = reverse_lazy('papers')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		if user.role == 'admin':
			pass
		elif user.role == 'lecturer':
			lecturer = Lecturer.objects.get(user=user)
			if lecturer.role == 'TL' or lecturer.role == 'hod':
				pass
			else:
				pass
		elif user.role == 'student':
			pass
		return context
	pass

class PaperUpdateView(LoginRequiredMixin, AdminMixin, UpdateView):
	model = Paper
	form_class = UpdatePaper
	template_name = 'results/base_form.html'
	success_url = reverse_lazy('papers')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		if user.role == 'admin':
			pass
		elif user.role == 'lecturer':
			lecturer = Lecturer.objects.get(user=user)
			if lecturer.role == 'TL' or lecturer.role == 'hod':
				pass
			else:
				pass
		elif user.role == 'student':
			pass
		return context
	pass

class ModulesViewList(LoginRequiredMixin, AdminOrLecturerMixin, ListView):
	model = Module
	template_name = 'results/modules.html'
	context_object_name = 'modules'
	paginate_by = 20

	def get_queryset(self):
		user = self.request.user
		if user.role == 'admin':
			qs = Module.objects.all()
		elif user.role == 'lecturer':
			specializations = Lecturer.objects.get(user=user).specializations.values_list('id', flat=True)
			papers = Paper.objects.filter(specialization__in=specializations).values_list('id', flat=True)
			qs = Module.objects.filter(paper__in=papers)
		return qs

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Modules'
		return context
	pass

class ModuleCreateView(LoginRequiredMixin, AdminMixin, CreateView):
	model = Module
	form_class = NewModule
	template_name = 'results/base_form.html'
	success_url = reverse_lazy('modules')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'New Module'
		return context
	pass

class ModuleUpdateView(LoginRequiredMixin, AdminMixin, UpdateView):
	model = Module
	form_class = UpdateModule
	template_name = 'results/base_form.html'
	success_url = reverse_lazy('modules')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		if user.role == 'admin':
			pass
		elif user.role == 'lecturer':
			lecturer = Lecturer.objects.get(user=user)
			if lecturer.role == 'TL' or lecturer.role == 'hod':
				pass
			else:
				pass
		elif user.role == 'student':
			pass
		return context
	pass

class ModuleScoresViewList(LoginRequiredMixin, ListView):
	model = ModuleScore
	template_name = 'results/modulescores.html'
	context_object_name = 'modulescores'
	paginate_by = 20

	def get_queryset(self):
		user = self.request.user
		paper = self.kwargs.get('paper')
		modules = Module.objects.filter(paper=paper).values_list('id', flat=True)
		qs = ModuleScore.objects.filter(module__in=modules)
		return qs

	def get_context_data(self, **kwargs):
		user = self.request.user
		paper_id = self.kwargs.get('paper')
		paper = Paper.objects.get(id=paper_id)
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Module Scores'
		context['paper'] = paper
		return context

class ModuleScoreCreateView(LoginRequiredMixin, AdminOrLecturerMixin, CreateView):
	model = ModuleScore
	form_class = NewModuleScore
	template_name = 'results/module_score.html'

	def get_success_url(self):
		return reverse_lazy('modulescores', kwargs={'paper': self.kwargs.get('paper')})

	def get_form_kwargs(self):
		kwargs = super(ModuleScoreCreateView, self).get_form_kwargs()
		kwargs['user'] = self.request.user
		kwargs['paper'] = self.kwargs.get('paper')
		return kwargs

	def get_context_data(self, **kwargs):
		user = self.request.user
		paper = self.kwargs.get('paper')
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'New Module Score'
		context['paper'] = Paper.objects.get(pk=paper)
		return context

	def post(self, request, *args, **kwargs):
		form = self.get_form(self.get_form_class())
		if form.is_valid:
			instance = form.save(commit=False)
			instance.added_by = self.request.user
			instance.save()
		return super().post(request, *args, **kwargs)

class ModuleScoreUpdateView(LoginRequiredMixin, AdminOrLecturerMixin, UpdateView):
	model = ModuleScore
	form_class = UpdateModuleScore
	template_name = 'results/base_form.html'

	def get_success_url(self):
		return reverse_lazy('modulescores', kwargs={'paper': self.kwargs.get('paper')})

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Edit Score'

		return context
	
	def form_valid(self, form):
		user = self.request.user
		form.instance.updated_by = user
		return super().form_valid(form)
	pass

class SitinsViewList(LoginRequiredMixin, ListView):
	model = SitinCat
	template_name = 'results/sitincats.html'
	context_object_name = 'sitincats'
	paginate_by = 20

	def get_queryset(self):
		user = self.request.user
		paper = self.kwargs.get('paper')
		qs = SitinCat.objects.filter(paper=paper)
		return qs

	def get_context_data(self, **kwargs):
		user = self.request.user
		paper_id = self.kwargs.get('paper')
		paper = Paper.objects.get(pk=paper_id)
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['paper'] = paper
		context['title'] = 'Sit-in Cats'
		return context

class SitinCreateView(LoginRequiredMixin, AdminOrLecturerMixin, CreateView):
	model = SitinCat
	form_class = NewSitinCat
	template_name = 'results/base_form.html'

	def get_success_url(self):
		return reverse_lazy('sitincats', kwargs={'paper': self.kwargs.get('paper')})

	def get_form_kwargs(self):
		kwargs = super(SitinCreateView, self).get_form_kwargs()
		kwargs['user'] = self.request.user
		kwargs['paper'] = self.kwargs.get('paper')
		return kwargs

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'New Sit-in Cat Score'
		return context

	def post(self, request, *args, **kwargs):
		form = self.get_form(self.get_form_class())
		if form.is_valid():
			instance = form.save(commit=False)
			instance.added_by = self.request.user
			instance.save()
		return super().post(request, *args, **kwargs)

class SitinUpdateView(LoginRequiredMixin, AdminOrLecturerMixin, UpdateView):
	model = SitinCat
	form_class = UpdateSitinCat
	template_name = 'results/base_form.html'

	def get_success_url(self):
		return reverse_lazy('sitincats', kwargs={'paper': self.kwargs.get('paper')})

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Update Sit-In'
		return context
	
	def form_valid(self, form):
		user = self.request.user
		form.instance.updated_by = user
		return super().form_valid(form)

class ResultViewList(LoginRequiredMixin, ListView):
	model = Result
	template_name = 'results/results.html'
	context_object_name = 'results'
	paginate_by = 20

	def get_queryset(self):
		user = self.request.user
		if user.role == 'admin':
			qs = Result.objects.all()
		elif user.role == 'lecturer':
			specializations = Lecturer.objects.get(user=user).specializations.values_list('id', flat=True)
			qs = Result.objects.filter(specialization__=specializations)
		return specializations.order_by('student')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Results'
		return context
	
class GenerateResults(LoginRequiredMixin, AdminOrLecturerMixin, FormView):
	model = Result
	template_name = 'results/generate_results.html'
	context_object_name = 'results'
	# form_class = 
	success_url = reverse_lazy('results')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Generate Results'
		return context
	
	def form_valid(self, form):
		user = self.request.user
		paper = form.paper
		generating_cat = form.cat
		combinations = CatCombination.objects.get(paper=paper)
		cat1_combinations = combinations.cat1.values_list('id', flat=True)
		cat2_combinations = combinations.cat2.values_list('id', flat=True)
		cat1_module_scores = ModuleScore.objects.filter(module__in=cat1_combinations)
		sitins = SitinCat.objects.filter(paper=paper)
		cat2_module_scores = ModuleScore.objects.filter(module__in=cat2_combinations)

		for score in cat1_module_scores:
			student = score.student
			cat = score.take_away + score.discussion
			obj, created = Result.objects.get_or_create(student=student, defaults={'paper':paper,'cat1':cat, 'added_by':user})
			if not created:
				initial = obj.cat1
				final = initial + cat
				obj.cat1 = final
				obj.save()

		for record in Result.objects.all():
			student = record.student
			discussion_takeaway = student.cat1
			final = discussion_takeaway + sitins.get(student=student).cat1
			student.cat1 = final
			student.save()

		return super().form_valid(form)

class TeamLeaderViewList(LoginRequiredMixin, AdminMixin, ListView):
	model = TeamLeader
	template_name = 'results/teamleaders.html'
	context_object_name = 'teamleaders'
	paginate_by = 20

	def get_queryset(self):
		return TeamLeader.objects.all()

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Team Leaders'
		return context

class TeamLeaderCreateView(LoginRequiredMixin, AdminMixin, CreateView):
	model = TeamLeader
	template_name = 'results/base_form.html'
	context_object_name = 'teamleaders'
	form_class = NewTeamLeader

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'New Team Leader'
		return context

class TeamLeaderUpdateView(LoginRequiredMixin, AdminMixin, UpdateView):
	model = TeamLeader
	template_name = 'results/base_form.html'
	context_object_name = 'teamleaders'
	form_class = UpdateTeamLeader

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Update Team Leader'
		return context

class HodViewList(LoginRequiredMixin, ListView):
	model = Hod
	template_name = 'results/hods.html'
	context_object_name = 'hods'
	paginate_by = 20

	def get_queryset(self):
		return Hod.objects.all()

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'HoDs'
		return context

class HodCreateView(LoginRequiredMixin, AdminMixin, CreateView):
	model = Hod
	template_name = 'results/base_form.html'
	context_object_name = 'hods'
	form_class = NewHoD
	success_url = reverse_lazy('hods')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'New HoD'
		return context

class HodUpdateView(LoginRequiredMixin, AdminMixin, UpdateView):
	model = Hod
	template_name = 'results/base_form.html'
	context_object_name = 'hods'
	form_class = UpdateHoD

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Update HoD'
		return context

class BulkStudentCreation(LoginRequiredMixin, AdminMixin, FormView):
	form_class = CSVUploadForm
	template_name = 'results/upload_csv.html'
	success_url = reverse_lazy('students') 

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'New bulk students'
		context['fields'] = ['admission', 'full_name', 'sex', 'mode', 'centre', 'specialization', 'date']
		return context

	def form_valid(self, form):
		user = self.request.user
		role = 'student'
		password = 'Kisedefault24'
		csv_file = self.request.FILES['csv_file']

		# Check if the file is a valid CSV
		if not csv_file.name.endswith('.csv'):
			messages.error(self.request, 'File is not CSV type')
			return redirect('upload_csv')

		# If the file is too large, handle that here
		if csv_file.multiple_chunks():
			messages.error(self.request, "Uploaded file is too big.")
			return redirect('upload_csv')

		# Process the CSV file
		print('uploaded')
		file_data = csv_file.read().decode("utf-8").splitlines()
		csv_reader = csv.reader(file_data)

		next(csv_reader) # skip the header row

		# Iterate over the rows in the CSV file and create the objects
		count = 0
		for row in csv_reader:
			if len(row) >= 7:  
				admission = row[0]
				full_name = row[1]
				sex = row[2]
				mode = row[3]
				centre = row[4]
				specialization = row[5]
				year = row[6]

				mode_id = Mode.objects.get(mode=mode)
				centre_id = Centre.objects.get(name=centre)
				specialization_id = Specialization.objects.get(code=specialization)
				user_instance = User.objects.create_user(username=admission, password=password, full_name=full_name, sex=sex, role=role)

				student = Student.objects.create(user=user_instance, admission=admission, mode=mode_id, centre=centre_id, added_by=user, year=year, specialization=specialization_id)
				count += 1

		messages.success(self.request, f'Added {count} Students Successfully')
		return super().form_valid(form)
	
class DeadlineViewList(LoginRequiredMixin, ListView):
	model = Deadline
	template_name = 'results/deadlines.html'
	context_object_name = 'deadlines'
	paginate_by = 20

	def get_queryset(self):
		return Deadline.objects.all()

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Deadlines'
		return context
	
class DeadlineCreateView(LoginRequiredMixin, AdminMixin, CreateView):
	model = Deadline
	template_name = 'results/base_form.html'
	form_class = NewDeadline

	def get_success_url(self):
		return reverse_lazy('deadlines')
	
	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Add Deadline'
		return context
	
	def post(self, request, *args, **kwargs):
		form = self.get_form(self.get_form_class())
		if form.is_valid():
			instance = form.save(commit=False)
			instance.deadline = form.cleaned_data['deadline']
			instance.added_by = self.request.user
			instance.save()
		return super().post(request, *args, **kwargs)

class DeadlineUpdateView(LoginRequiredMixin, AdminMixin, UpdateView):	
	model = Deadline
	template_name = 'results/base_form.html'
	form_class = UpdateDeadline
	success_url = reverse_lazy('deadlines')
	
	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Update Deadline'
		return context
	
	def form_valid(self, form):
		user = self.request.user
		form.instance.updated_by = user
		return super().form_valid(form)
	
class CatCombinationsViewList(LoginRequiredMixin, AdminOrLecturerMixin, ListView):
	model = CatCombination
	template_name = 'results/cat_combinations.html'
	context_object_name = 'cat_combinations'
	paginate_by = 50

	def get_queryset(self):
		user = self.request.user
		if user.role == 'admin':
			qs = CatCombination.objects.all()
		elif user.role == 'lecturer':
			specializations = Lecturer.objects.get(user=user).specializations.values_list('id', flat=True)
			papers = Paper.objects.filter(specialization__in=specializations).values_list('id', flat=True)
			qs = CatCombination.objects.filter(paper__in=papers)
		return qs
	
	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Cat Combinations'
		return context
	
class CatCombinationCreateView(LoginRequiredMixin, AdminMixin, CreateView):
	model = CatCombination
	template_name = 'results/base_form.html'
	form_class = NewCatCombination

	def get_success_url(self):
		return reverse_lazy('cat_combinations')
	
	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Add Cat Combination'
		return context
	
	def post(self, request, *args, **kwargs):
		form = self.get_form(self.get_form_class())
		if form.is_valid():
			form.save()
		return super().post(request, *args, **kwargs)

class CatCombinationUpdateView(LoginRequiredMixin, AdminMixin, UpdateView):	
	model = CatCombination
	template_name = 'results/base_form.html'
	form_class = UpdateCatCombination
	success_url = reverse_lazy('cat_combinations')
	
	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Update Deadline'
		return context
	
class DeactivateUser(LoginRequiredMixin, AdminMixin, View):
	def post(self, request, user_id, *args, **kwargs):

		user = get_object_or_404(User, id=user_id)

		user.is_active = False
		user.save()

		messages.success(request, f'User {user.full_name} has been deactivated.')

		return redirect('lecturers')
	
class ActivateUser(LoginRequiredMixin, AdminMixin, View):
	def post(self, request, user_id, *args, **kwargs):

		user = get_object_or_404(User, id=user_id)

		user.is_active = True
		user.save()

		messages.success(request, f'User {user.full_name} has been Activated.')

		return redirect('lecturers')

def custom_403_view(request, exception):
	return render(request, 'errors/403.html', status=403, context={'title': 403})

def custom_404_view(request, exception):
	return render(request, 'errors/404.html', status=404, context={'title': 404})

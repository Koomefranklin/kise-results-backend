from typing import Any
from django.contrib.auth.views import LoginView
from django.db.models.query import QuerySet
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, CreateView, FormView, UpdateView
from django.db.models import Q, Avg, F, ExpressionWrapper, FloatField, Value
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models.functions import Coalesce

from teaching_practice.mailer import send_error, send_otp
from .mixins import AdminMixin, AdminOrHeadMixin, AdminOrLecturerMixin, HoDMixin
from .models import Deadline, Hod, ModuleScore, ResetPasswordOtp, User, Student, Result, Mode, Lecturer, Specialization, Paper, TeamLeader, Module, CatCombination, IndexNumber, SitinCat, Centre
from django.http.response import HttpResponse
from .forms import CSVUploadForm, CustomLoginForm, CustomPasswordChangeForm, CustomUserCreationForm, CustomUserChangeForm, GenerateResultsForm, NewCatCombination, NewDeadline, NewHoD, NewStudent, NewTeamLeader, OTPVerificationForm, ResetPasswordForm, UpdateCatCombination, UpdateDeadline, UpdateHoD, UpdateStudent, NewLecturer, UpdateLecturer, NewSpecialization, UpdateSpecialization, NewPaper, UpdatePaper, NewModule, UpdateModule, NewModuleScore, UpdateModuleScore, NewSitinCat, UpdateSitinCat, UpdateTeamLeader, SearchForm
from itertools import chain
from dal import autocomplete
from django.urls import reverse_lazy
from django.contrib import messages
import csv
from django.utils.crypto import get_random_string

# Create your views here.
@login_required
def CommonBase(request):
	return render(request,'common/index.html')

class StudentAutocomplete(autocomplete.Select2QuerySetView):
	def get_queryset(self):
		user = self.request.user
		paper = self.forwarded.get('paper', None)
		specializations = Lecturer.objects.get(user=user).specializations.values_list('id', flat=True)
		qs = Student.objects.filter(Q(specialization__in=specializations) & Q(user__is_active=True))
		if self.q:
			qs = qs.filter(Q(user__full_name__icontains=self.q) | Q(admission__icontains=self.q))
		if paper:
			specialization = Paper.objects.get(pk=paper).specialization
			qs = qs.filter(specialization=specialization)
		return qs

class LecturerAutocomplete(autocomplete.Select2QuerySetView):
	def get_queryset(self):
		qs = Lecturer.objects.filter(user__is_active=True)
		if self.q:
			qs = qs.filter(Q(user__full_name__icontains=self.q) | Q(specializations__name__icontains=self.q))
		return qs

class ModuleAutocomplete(autocomplete.Select2QuerySetView):
	def get_queryset(self):
		user = self.request.user
		if user.role == 'admin':
			qs = Module.objects.all()
		elif user.role == 'lecturer':
			specializations = Lecturer.objects.filter(Q(user=user) & Q(user__is_active=True)).values_list('id', flat=True)
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
			students = Student.objects.filter(user__is_active=True).count()
			lecturers = Lecturer.objects.filter(user__is_active=True).count()
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
				students = Student.objects.filter(Q(center=tl.center) & Q(user__is_active=True)).count()
				lecturers = Lecturer.objects.filter(user__is_active=True).count()
				all_specializations = Specialization.objects.filter(mode__in=dl).values_list('id', flat=True)
				all_papers = Paper.objects.filter(specialization__in=all_specializations).values_list('id')
				modules = Module.objects.filter(paper__in=all_papers).count()
				specializations = all_specializations.count()
				papers = all_papers.count()
			elif lecturer in hods:
				hod = Hod.objects.get(lecturer=lecturer)
				students = Student.objects.filter(Q(specialization=hod.specialization) & Q(user__is_active=True)).count()
				lecturers = Lecturer.objects.filter(user__is_active=True).count()
				all_specializations = lecturer.specializations
				all_papers = Paper.objects.filter(specialization__in=all_specializations).values_list('id')
				modules = Module.objects.filter(paper__in=all_papers).count()
				specializations = all_specializations.count()
				papers = all_papers.count()
			else:
				all_specializations = lecturer.specializations.values_list('id', flat=True)
				students = Student.objects.filter(Q(specialization__in=all_specializations) & Q(user__is_active=True)).count()
				lecturers = Lecturer.objects.filter(user__is_active=True).count()
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
	
class CustomLoginView(LoginView):
    form_class = CustomLoginForm

class UpdateUserPassword(LoginRequiredMixin, FormView):
	form_class = CustomPasswordChangeForm
	template_name = 'registration/change_password.html'
	success_url = reverse_lazy('common')

	def get_form_kwargs(self):
		kwargs = super(UpdateUserPassword, self).get_form_kwargs()
		kwargs['user'] = self.request.user
		return kwargs
	
	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['title'] = 'Password Change'
		return context
	
class FirstTimePasswordChangeView(UpdateUserPassword):
	template_name = 'registration/change_password_first.html'
	success_url = reverse_lazy('students_tp')

	def form_valid(self, form):
		response = super().form_valid(form)
		user = self.request.user
		user.set_password(form.cleaned_data['new_password1'])
		user.is_first_login = False
		user.save()
		return response
	
class ResetpaswordRequestView(FormView):
	form_class = ResetPasswordForm
	template_name = 'registration/reset_password.html'

	def get_success_url(self):
		return reverse_lazy('reset_password')
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['title'] = 'Reset Password'
		context['stage'] = 'request'
		return context
	
	def get_form_kwargs(self):
		kwargs = super(ResetpaswordRequestView, self).get_form_kwargs()
		kwargs['username'] = self.request.GET.get('username')
		return kwargs

	def form_valid(self, form):
		username = form.cleaned_data['username']
		user = User.objects.get(username=username)

		user.set_unusable_password()
		user.save()
		otp = get_random_string(6)
		obj, created = ResetPasswordOtp.objects.get_or_create(user=user, defaults={'otp': otp})
		if not created:
			expiry = obj.expiry

			if expiry < timezone.now():
				obj.delete()
				otp = get_random_string(6)
				obj = ResetPasswordOtp.objects.create(user=user, otp=otp)

		send_otp(self.request, obj)
		return redirect(reverse_lazy('reset_password', kwargs={'username': username}))

class ResetPasswordView(FormView):
	form_class = OTPVerificationForm
	template_name = 'registration/reset_password.html'
	success_url = reverse_lazy('login')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['title'] = 'Reset Password'
		context['stage'] = 'reset'
		return context
	
	def get_form_kwargs(self):
		kwargs = super(ResetPasswordView, self).get_form_kwargs()
		kwargs['otp'] = self.request.GET.get('otp')
		return kwargs
	
	def form_valid(self, form):
		response = super().form_valid(form)
		username = self.kwargs.get('username')
		otp = form.cleaned_data['otp']
		password = form.cleaned_data['new_password']
		try:
			otp_obj = ResetPasswordOtp.objects.get(user__username=username)
			user = otp_obj.user
			generated_otp = otp_obj.otp
			otp_expiry = otp_obj.expiry
			if otp_expiry < timezone.now():
				otp_obj.delete()
				messages.error(self.request, 'OTP expired. Request a new one')
				raise ResetPasswordOtp.DoesNotExist()
			else:
				if otp == generated_otp:
					user.set_password(password)
					user.save()
					otp_obj.delete()
					messages.success(self.request, 'Password Reset Successful')
				else:
					messages.error(self.request, 'Invalid OTP')
					return self.form_invalid(self.get_form_class())
		except ResetPasswordOtp.DoesNotExist:
			return redirect(f'{reverse_lazy('request_otp')}?username={username}')
		return response

class StudentsViewList(LoginRequiredMixin, ListView):
	model = Student
	template_name = 'results/students.html'
	context_object_name = 'students'
	paginate_by = 50

	def get_queryset(self):
		user = self.request.user
		search_query = self.request.GET.get('search_query')
		if user.role == 'admin':
			qs = Student.objects.all()
		elif user.role == 'lecturer':
			specializations = Lecturer.objects.get(user=user).specializations.values_list('id', flat=True)
			qs = Student.objects.filter(specialization__in=specializations)
		if search_query:
			qs = qs.filter(Q(user__full_name__icontains=search_query) | Q(admission__icontains=search_query))
		return qs.order_by('admission')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Students'
		context['search_query'] = SearchForm(self.request.GET)
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
		context['title'] = 'Add Student'
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
		search_query = self.request.GET.get('search_query')
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
		if search_query:
			qs = qs.filter(user__full_name__icontains=search_query)
		return qs

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Lecturers'
		context['search_query'] = SearchForm(self.request.GET)
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
		context['title'] = 'Add Lecturer'
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
		search_query = self.request.GET.get('search_query')
		if user.role == 'admin':
			qs = Specialization.objects.all()
		elif user.role == 'lecturer':
			specializations = Lecturer.objects.get(user=user).specializations.values_list('id', flat=True)
			qs = Specialization.objects.filter(pk__in=specializations)
		if search_query:
			qs = qs.filter(Q(name__icontains=search_query) | Q(code__icontains=search_query))
		return qs.order_by('code')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Specializations'
		context['search_query'] = SearchForm(self.request.GET)
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
		search_query = self.request.GET.get('search_query')
		specialization = self.request.GET.get('sp')
		if user.role == 'admin':
			qs = Paper.objects.all().order_by('code')
		elif user.role == 'lecturer':
			specializations = Lecturer.objects.get(user=user).specializations.values_list('id', flat=True)
			qs = Paper.objects.filter(specialization__in=specializations)
		if specialization:
			qs = qs.filter(specialization=specialization)
		if search_query:
			qs = qs.filter(Q(code__icontains=search_query) | Q(name__icontains=search_query) | Q(specialization__name__icontains=search_query))
		return qs.order_by('code')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Papers'
		context['search_query'] = SearchForm(self.request.GET)
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
	paginate_by = 40

	def get_queryset(self):
		user = self.request.user
		search_query = self.request.GET.get('search_query')
		query = self.request.GET.get('query')
		if user.role == 'admin':
			qs = Module.objects.all()
		elif user.role == 'lecturer':
			specializations = Lecturer.objects.get(user=user).specializations.values_list('id', flat=True)
			papers = Paper.objects.filter(specialization__in=specializations).values_list('id', flat=True)
			qs = Module.objects.filter(paper__in=papers)
		if query:
			qs = qs.filter(paper=query)
		if search_query:
			qs = qs.filter(Q(code__icontains=search_query) | Q(name__icontains=search_query) | Q(paper__code__icontains=search_query) | Q(paper__name__icontains=search_query))
		return qs.order_by('paper')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Modules'
		context['search_query'] = SearchForm(self.request.GET)
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
		context['title'] = 'Add Module'
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
		search_query = self.request.GET.get('search_query')
		paper = self.kwargs.get('paper')
		modules = Module.objects.filter(paper=paper).values_list('id', flat=True)
		qs = ModuleScore.objects.filter(module__in=modules)
		if search_query:
			qs = qs.filter(Q(student__admission__icontains=search_query) | Q(student__user__full_name__icontains=search_query) | Q(module__name__icontains=search_query) | Q(module__paper__name__icontains=search_query))
		return qs

	def get_context_data(self, **kwargs):
		user = self.request.user
		paper_id = self.kwargs.get('paper')
		paper = Paper.objects.get(id=paper_id)
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Module Scores'
		context['paper'] = paper
		context['search_query'] = SearchForm(self.request.GET)
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
		context['title'] = 'Add Module Score'
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

class SitinsViewList(LoginRequiredMixin, ListView):
	model = SitinCat
	template_name = 'results/sitincats.html'
	context_object_name = 'sitincats'
	paginate_by = 20

	def get_queryset(self):
		user = self.request.user
		search_query = self.request.GET.get('search_query')
		paper = self.kwargs.get('paper')
		qs = SitinCat.objects.filter(paper=paper)
		if search_query:
			qs = qs.filter(Q(student__admission__icontains=search_query) | Q(student__user__full_name__icontains=search_query))
		return qs

	def get_context_data(self, **kwargs):
		user = self.request.user
		paper_id = self.kwargs.get('paper')
		paper = Paper.objects.get(pk=paper_id)
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['paper'] = paper
		context['title'] = 'Sit-in Cats'
		context['search_query'] = SearchForm(self.request.GET)
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
		context['title'] = 'Add Sit-in Cat Score'
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
	paginate_by = 50

	def get_queryset(self):
		user = self.request.user
		search_query = self.request.GET.get('search_query')
		if user.role == 'admin':
			qs = Result.objects.all()
		elif user.role == 'lecturer':
			specializations = Lecturer.objects.get(user=user).specializations.values_list('id', flat=True)
			qs = Result.objects.filter(paper__specialization__in=specializations)
		if search_query:
			qs = qs.filter(Q(student__admission__icontains=search_query) | Q(student__user__full_name__icontains=search_query)| Q(paper__code__icontains=search_query) | Q(paper__name__icontains=search_query) | Q(paper__specialization__name__icontains=search_query))
		return qs.order_by('student')

	def get_context_data(self, **kwargs):
		user = self.request.user
		hod = Hod.objects.filter(lecturer__user=user).first()
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Results'
		context['search_query'] = SearchForm(self.request.GET)
		context['hod'] = hod
		return context
	
class GenerateResults(LoginRequiredMixin, HoDMixin, FormView):
	model = Result
	template_name = 'results/base_form.html'
	context_object_name = 'results'
	form_class = GenerateResultsForm
	success_url = reverse_lazy('results')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Generate Results'
		return context
	
	def get_form_kwargs(self):
		kwargs = super(GenerateResults, self).get_form_kwargs()
		kwargs['user'] = self.request.user
		return kwargs
	
	def form_valid(self, form):
		user = self.request.user
		paper = form.cleaned_data['paper']
		cat = form.cleaned_data['cat']
		specialization = Paper.objects.get(pk=paper.pk).specialization
		students = Student.objects.filter(Q(specialization=specialization) & Q(user__is_active=True))
		all_modules = CatCombination.objects.get(paper=paper)

		if cat == 'cat1':
			modules = all_modules.cat1.all()
			module_scores = ModuleScore.objects.filter(module__in=modules)

			for student in students:
				try:
					sitin = SitinCat.objects.get(Q(student=student) & Q(paper=paper)).cat1
				except SitinCat.DoesNotExist:
					sitin = 0
				student_score = module_scores.filter(student=student).annotate(avg_discussion_takeaway=ExpressionWrapper(
					(Coalesce(F('discussion'), Value(0)) + Coalesce(F('take_away'), Value(0))) / 2.0,
        	output_field=FloatField())).aggregate(total=Avg('avg_discussion_takeaway', default=0))['total']
				
				final_score = student_score + sitin
				
				obj, created = Result.objects.update_or_create(
					student = student,
					paper = paper,
					defaults={'cat1': final_score, 'added_by': user}
				)

		elif cat == 'cat2':
			modules = all_modules.cat2.all()
			module_scores = ModuleScore.objects.filter(pk__in=modules)

			for student in students:
				try:
					sitin = SitinCat.objects.get(Q(student=student) & Q(paper=paper)).cat2
				except SitinCat.DoesNotExist:
					sitin = 0
				student_score = module_scores.filter(student=student).annotate(avg_discussion_takeaway=ExpressionWrapper(
					(Coalesce(F('discussion'), Value(0)) + Coalesce(F('take_away'), Value(0))) / 2.0,
        	output_field=FloatField())).aggregate(total=Avg('avg_discussion_takeaway', default=0))['total']
				
				final_score = student_score + sitin

				obj, created = Result.objects.update_or_create(
					student = student,
					paper = paper,
					defaults={'cat2': final_score, 'added_by': user}
				)

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
		context['search_query'] = SearchForm(self.request.GET)
		return context

class TeamLeaderCreateView(LoginRequiredMixin, AdminMixin, CreateView):
	model = TeamLeader
	template_name = 'results/base_form.html'
	context_object_name = 'teamleaders'
	form_class = NewTeamLeader

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Add Team Leader'
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
		context['search_query'] = SearchForm(self.request.GET)
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
		context['title'] = 'Add HoD'
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
		context['title'] = 'Add bulk students'
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
		file_data = csv_file.read().decode("utf-8").splitlines()
		csv_reader = csv.reader(file_data)

		next(csv_reader) # skip the header row

		# Iterate over the rows in the CSV file and create the objects
		count = 0
		for row in csv_reader:
			if len(row) >= 7:  
				admission = row[0]
				try:
					User.objects.get(username=admission)
				except:
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
	paginate_by = 20

	def get_queryset(self):
		user = self.request.user
		search_query = self.request.GET.get('search_query')
		if user.role == 'admin':
			qs = CatCombination.objects.all().order_by('paper')
		elif user.role == 'lecturer':
			specializations = Lecturer.objects.get(user=user).specializations.values_list('id', flat=True)
			papers = Paper.objects.filter(specialization__in=specializations).values_list('id', flat=True)
			qs = CatCombination.objects.filter(paper__in=papers)
		if search_query:
			qs = qs.filter(Q(paper__name__icontains=search_query) | Q(paper__code__icontains=search_query))
		return qs
	
	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Cat Combinations'
		context['search_query'] = SearchForm(self.request.GET)
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

	def get_form_kwargs(self):
		kwargs = super(CatCombinationUpdateView, self).get_form_kwargs()
		kwargs['user'] = self.request.user
		kwargs['combination'] = self.kwargs.get('pk')
		return kwargs
	
	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Update Cat Combination'
		return context
	
class DeactivateUser(LoginRequiredMixin, AdminMixin, View):
	def post(self, request, user_id, *args, **kwargs):

		user = get_object_or_404(User, id=user_id)

		user.is_active = False
		user.save()

		messages.success(request, f'User {user.full_name} has been deactivated.')

		return HttpResponseRedirect(self.request.get_full_path())
	
class ActivateUser(LoginRequiredMixin, AdminMixin, View):
	def post(self, request, user_id, *args, **kwargs):

		user = get_object_or_404(User, id=user_id)

		user.is_active = True
		user.save()

		messages.success(request, f'User {user.full_name} has been Activated.')

		return HttpResponseRedirect(self.request.get_full_path())
	
def redirect_tp(request):
	return redirect('index')

def custom_403_view(request, exception):
	return render(request, 'errors/403.html', status=403, context={'title': 403})

def custom_404_view(request, exception):
	return render(request, 'errors/404.html', status=404, context={'title': 404})

def custom_500_view(request):
	send_error(request, getattr(request, 'exception', None))
	return render(request, 'errors/500.html', status=500, context={'title': 'Server error'})

from collections import defaultdict
import csv
import datetime
from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchVector
from django.core.exceptions import MultipleObjectsReturned, PermissionDenied
from django.db.models.sql import Query
from django.shortcuts import get_object_or_404, render, redirect
from dal import autocomplete
from django.template.context_processors import media
from django.utils import timezone
from django.views.generic.base import View
from django.urls import reverse_lazy
from dev.forms import CustomUserCreationForm
from dev.mixins import HoDMixin
from dev.models import Hod, User
from teaching_practice.mailer import request_deletion, send_student_report
from teaching_practice.mixins import ActivePeriodMixin, AdminHeadMixin, AdminMixin
from .forms import AspectFilterForm, CertificateStudentForm, FilterAssessmentsForm, NewAspect, NewCertificateStudentLetterForm, NewLocationForm, NewSection, NewStudentAspect, NewStudentForm, NewDiplomaStudentLetterForm, NewStudentSection, NewSubSection, PeriodForm, SearchForm, DiplomaStudentForm, StudentFilterForm, UpdateAspect, UpdateCertificateStudentLetter, UpdateSection, UpdateStudentAspect, UpdateDiplomaStudentLetter, UpdateStudentForm, UpdateStudentSection, StudentAspectFormSet, UpdateSubSection, ZonalLeaderForm
from .models import AssessmentType, Period, Student, Section, StudentAspect, StudentLetter, StudentSection, Aspect, Location, SubSection, ZonalLeader
from django.views.generic import ListView, CreateView, FormView, UpdateView, DeleteView, DetailView
from django.db.models import Q, Avg, F, Count, ExpressionWrapper, FloatField, Sum, Value
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.gis.geos import Point
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django_weasyprint import WeasyTemplateResponseMixin
import tempfile
from django.db.models.fields import Field
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType


# Create your views here.

def log_custom_action(user, obj, action=CHANGE):
	LogEntry.objects.log_action(
		user_id=user.pk,
		content_type_id=ContentType.objects.get_for_model(obj).pk,
		object_id=obj.pk,
		object_repr=str(obj),
		action_flag=action,
	)

class StudentAutocomplete(autocomplete.Select2QuerySetView):
	def get_queryset(self):
		user = self.request.user
		qs = User.objects.filter(Q(is_active=True) | Q(role='student'))
		if self.q:
			qs = qs.filter(Q(full_name__icontains=self.q))
		return qs
	
class LecturerAutocomplete(autocomplete.Select2QuerySetView):
	def get_queryset(self):
		user = self.request.user
		qs = User.objects.filter(Q(is_active=True) & Q(role='lecturer'))
		if self.q:
			qs = qs.filter(Q(full_name__icontains=self.q))
		return qs
	
class NewPeriodView(LoginRequiredMixin, AdminMixin, CreateView):
	model = Period
	template_name = 'teaching_practice/periods.html'
	form_class = PeriodForm
	success_url = reverse_lazy('new_period')

	def get_context_data(self, **kwargs):
		periods = Period.objects.all()
		context = super().get_context_data(**kwargs)
		context['title'] = 'New Period'
		context['is_nav_enabled'] = True
		context['periods'] = periods
		return context

	def post(self, request, *args, **kwargs):
		form = self.get_form(self.get_form_class())
		if form.is_valid:
			instance = form.save(commit=False)
			instance.created_by = self.request.user
			instance.save()
			log_custom_action(self.request.user, instance, ADDITION)
			messages.success(request, f'Period {instance.period} created successfuly')
			self.object = instance
			return HttpResponseRedirect(self.get_success_url())
		else:
			return self.form_invalid(form)

class EditPeriodView(LoginRequiredMixin, AdminMixin, UpdateView):
	model = Period
	template_name = 'teaching_practice/periods.html'
	form_class = PeriodForm
	success_url = reverse_lazy('new_period')

	def get_context_data(self, **kwargs):
		periods = Period.objects.all()
		current_period = Period.objects.get(pk=self.kwargs.get('pk'))
		context = super().get_context_data(**kwargs)
		context['title'] = f'Edit Period {current_period.period}'
		context['is_nav_enabled'] = True
		context['periods'] = periods
		return context
	
	def form_valid(self, form):
		
		if form.is_valid:
			instance = form.save(commit=False)
			instance.updated_by = self.request.user
			instance.save()
			log_custom_action(self.request.user, instance, CHANGE)
			messages.success(self.request, f'Period {instance.period} updated successfuly')
			self.object = instance
			return HttpResponseRedirect(self.get_success_url())
		else:
			return self.form_invalid(form)
	
class AssessorsViewList(LoginRequiredMixin, AdminMixin, ListView):
	model = User
	template_name = 'teaching_practice/assessors.html'
	paginate_by = 50

	def get_queryset(self):
		get_request = self.request.GET
		qs = User.objects.filter(Q(role='lecturer') & Q(is_active=True))
		if search_query := get_request.get('search_query'):
			qs = qs.filter(full_name__icontains=search_query)
		return qs

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Assessors'
		context['search_query'] = SearchForm(self.request.GET)
		return context

class IndexPage(LoginRequiredMixin, ListView):
	model = User
	template_name = 'teaching_practice/index.html'
	context_object_name = 'dashboard'

	def get_queryset(self):
		return User.objects.filter(pk=self.request.user.pk)
	
	def get_context_data(self, **kwargs):
		user = self.request.user
		zonal_leaders = ZonalLeader.objects.all().values_list('assessor', flat=True)
		students = Student.objects.all()
		all_assessments = StudentLetter.objects.filter(to_delete=False)
		assessment_types = AssessmentType.objects.all()
		admins = assessment_types.values_list('admins', flat=True)
		if user.is_superuser:
			initiated_assessments = all_assessments
		elif user.pk in admins:
			admin_assessment_types = assessment_types.filter(admins=user)
			initiated_assessments = all_assessments.filter(assessment_type__in=admin_assessment_types)
		else:
			if user.pk in zonal_leaders:
				initiated_assessments = all_assessments.filter(assessor=user)
			else:
				initiated_assessments = all_assessments.filter(assessor=user)

		period_students = students
		letters = initiated_assessments.distinct('student')
		completed_assessments = initiated_assessments.exclude(comments=None)
		pending_assessments = initiated_assessments.filter(comments=None)
		sections = Section.objects.all()
		aspects = Aspect.objects.all()

		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Teaching Practice Home'
		context['letters'] = letters.count()
		context['initiated_assessments'] = initiated_assessments.count()
		context['students'] = students.count()
		context['sections'] = sections.count()
		context['aspects'] = aspects.count()
		context['completed_assessments'] = completed_assessments.count()
		context['pending_assessments'] = pending_assessments.count()
		return context

class NewSectionView(LoginRequiredMixin, AdminMixin, CreateView):
	model = Section
	form_class = NewSection
	template_name = 'teaching_practice/base_form.html'
	success_url = reverse_lazy('sections')
	
	def get_form_kwargs(self):
		kwargs = super(NewSectionView, self).get_form_kwargs()
		kwargs['user'] = self.request.user
		return kwargs
	
	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		return context
	
	def post(self, request, *args, **kwargs):
		form = self.get_form(self.get_form_class())
		if form.is_valid:
			instance = form.save(commit=False)
			instance.created_by = self.request.user
			instance.save()
			self.object = instance
			return HttpResponseRedirect(self.get_success_url())
		else:
			return self.form_invalid(form)

class EditsectionView(LoginRequiredMixin, AdminMixin, UpdateView):
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
	paginate_by = 50

	def get_queryset(self):
		get_request = self.request.GET
		qs = Section.objects.all()
		search_query = get_request.get('search_query')
		if search_query:
			qs = qs.filter(Q(name__icontains=search_query) | Q(score__icontains=search_query))
		return qs.order_by('assessment_type', 'number')
	
	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Sections'
		context['search_query'] = SearchForm(self.request.GET)
		return context
	
class NewSubSectionView(LoginRequiredMixin, AdminMixin, CreateView):
	model = SubSection
	form_class = NewSubSection
	template_name = 'teaching_practice/base_form.html'
	success_url = reverse_lazy('sub_sections')
	
	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'New Sub-Section'
		return context

class EditSubSectionView(LoginRequiredMixin, AdminMixin, UpdateView):
	model = SubSection
	form_class = UpdateSubSection
	template_name = 'teaching_practice/base_form.html'
	success_url = reverse_lazy('sub_sections')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Edit Sub-Section'
		return context
	
class SubSectionViewlist(LoginRequiredMixin, ListView):
	model = SubSection
	template_name = 'teaching_practice/sub_sections.html'
	context_object_name = 'sub_sections'
	paginate_by = 50

	def get_queryset(self):
		get_request = self.request.GET
		qs = SubSection.objects.all()
		search_query = get_request.get('search_query')
		if search_query:
			qs = qs.filter(Q(name__icontains=search_query) | Q(section__name__icontains=search_query))
		return qs.order_by('section')
	
	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Sub-Sections'
		context['search_query'] = SearchForm(self.request.GET)
		return context

class NewAspectView(LoginRequiredMixin, AdminMixin, CreateView):
	model = Aspect
	form_class = NewAspect
	template_name = 'teaching_practice/base_form.html'
	success_url = reverse_lazy('aspects')

	def get_form_kwargs(self):
		kwargs = super(NewAspectView, self).get_form_kwargs()
		kwargs['user'] = self.request.user
		return kwargs

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'New Aspect'
		return context
	
	def post(self, request, *args, **kwargs):
		form = self.get_form(self.get_form_class())
		if form.is_valid:
			instance = form.save(commit=False)
			instance.created_by = self.request.user
			instance.save()
			log_custom_action(self.request.user, instance, ADDITION)
			self.object = instance
			return HttpResponseRedirect(self.get_success_url())
		else:
			return self.form_invalid(form)

class EditAspectView(LoginRequiredMixin, AdminMixin, UpdateView):
	model = Aspect
	form_class = UpdateAspect
	template_name = 'teaching_practice/base_form.html'
	success_url = reverse_lazy('aspects')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Edit Aspects to consider'
		return context

class AspectViewList(LoginRequiredMixin, ListView):
	model = Aspect
	template_name = 'teaching_practice/aspects.html'
	context_object_name = 'aspects'
	paginate_by = 70

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Aspects to consider'
		context['search_query'] = SearchForm(self.request.GET)
		context['filter_form'] = AspectFilterForm(self.request.GET)
		context['total'] = self.get_queryset().aggregate(contribution_sum = Sum('contribution'))['contribution_sum'] 
		return context
	
	def get_queryset(self):
		get_request = self.request.GET
		qs = Aspect.objects.all()
		search_query = get_request.get('search_query')
		if search_query:
			qs = qs.filter(Q(name__icontains=search_query) | Q(section__name__icontains=search_query))
		if assessment_type := get_request.get('assessment_type'):
			qs = qs.filter(section__assessment_type=assessment_type)
		if section := get_request.get('section'):
			qs = qs.filter(section__pk=section)
		return qs.order_by('section')
	
class NewStudentView(LoginRequiredMixin, ActivePeriodMixin, CreateView):
	model = Student
	form_class = NewStudentForm
	template_name = 'teaching_practice/base_form.html'
	success_url = reverse_lazy('students_tp')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'New Student'
		return context
	
	def post(self, request, *args, **kwargs):
		form = self.get_form(self.get_form_class())
		if form.is_valid():
			instance = form.save(commit=False)
			instance.created_by = self.request.user
			active_period=Period.objects.get(is_active=True)
			instance.period = active_period
			instance.save()

			log_custom_action(self.request.user, instance, ADDITION)
			self.object = instance
			messages.success(self.request, f'Added {instance.full_name} Successfully')
			return redirect(f"{reverse_lazy('students_tp')}?search_query={instance.index}")
		else:
			self.object = None
			return self.form_invalid(form)
	
class EditStudentView(LoginRequiredMixin, ActivePeriodMixin, UpdateView):
	model = Student
	form_class = UpdateStudentForm
	template_name = 'teaching_practice/base_form.html'
	success_url = reverse_lazy('students_tp')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Edit Student'
		return context
	
class StudentsViewList(LoginRequiredMixin, ListView):
	model = Student
	template_name = 'teaching_practice/students.html'
	context_object_name = 'students'
	paginate_by = 50
	
	def get_context_data(self, **kwargs):
		get_request = self.request.GET
		user = self.request.user
		searched = get_request.get('search_query')
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Students'
		context['search_query'] = SearchForm(self.request.GET)
		context['location_form'] = NewLocationForm(self.request.POST)
		context['filter_form'] = StudentFilterForm(self.request.GET)
		context['searched'] = True if searched else False
		context['types'] = list(AssessmentType.objects.all().values('id', 'short_name', 'name', 'course__code'))
		return context
	
	def get_queryset(self):
		get_request = self.request.GET
		active_period = Period.objects.get(is_active=True)
		qs = Student.objects.filter(period=active_period).annotate(search=SearchVector('full_name', 'index', 'email'))
		search_query = get_request.get('search_query')
		if search_query:
			query = SearchQuery(search_query)
			qs = qs.filter(search=query)
		if filter_query := get_request.get('filter_query'):
			duplicates = qs.values(filter_query).annotate(dup_count=Count(filter_query)).filter(dup_count__gt=1)
			duplicate_ids = [item[filter_query] for item in duplicates]
			if filter_query == 'index':
				qs = qs.filter(index__in=duplicate_ids)
			else:
				qs = qs.filter(full_name__in=duplicate_ids)
		return qs.order_by('index')

class DeleteStudent(LoginRequiredMixin, View):
	def get(self, request, student_id, *args, **kwargs):
		student = Student.objects.get(pk=student_id)
		letters = Student.objects.prefetch_related('letters').filter(pk=student_id)
		context = {
			'link': 'delete_student',
			'obj': letters
		}
		
		return(render(request, 'teaching_practice/delete.html', context=context))

	def post(self, request, student_id, *args, **kwargs):
		student = Student.objects.get(pk=student_id)
		student.delete()
		log_custom_action(self.request.user, student, DELETION)
		messages.success(request, f'Student {student.full_name} Deleted')
		return redirect(f'{reverse_lazy('students_tp')}?filter_query=index')

class NewStudentLetterView(LoginRequiredMixin, ActivePeriodMixin, View):
	def post(self, request, *args, **kwargs):
		longitude = self.kwargs.get('longitude')
		latitude = self.kwargs.get('latitude')
		student_id = self.kwargs.get('student_id')
		assessment_type_id = self.kwargs.get('assessment_type')
		deadline = timezone.datetime.strptime('17:00', '%H:%M').time()
		start_time = timezone.datetime.strptime('08:00', '%H:%M').time()
		current_time = timezone.datetime.now().astimezone().time()
		assessment_type = AssessmentType.objects.get(pk=assessment_type_id)

		if latitude and longitude:
			try:
				point = Point(float(longitude), float(latitude))
				location_instance = Location.objects.create(point=point)
			except ValueError:
				location_instance = None
		else:
			location_instance = None

		student_instance = Student.objects.get(pk=student_id)

		try:
			student_letter, created = StudentLetter.objects.get_or_create(student=student_instance, 
				assessor=self.request.user, to_delete=False, assessment_type=assessment_type, defaults={'location':location_instance})
			if not created:
				previous_assessment_type = student_letter.assessment_type.id
				creation_time = student_letter.created_at
				time_difference = timezone.now() - creation_time
				if time_difference.days < 4 and assessment_type_id == previous_assessment_type:
					return redirect(reverse_lazy('edit_student_letter', kwargs={'pk': student_letter.pk}))
				else:
					student_letter = StudentLetter.objects.create(student=student_instance, assessor=self.request.user, assessment_type=assessment_type, location=location_instance)
					log_custom_action(self.request.user, student_letter, ADDITION)
					
			location_instance.save()
			log_custom_action(self.request.user, location_instance, ADDITION)
			if not (current_time > start_time <= current_time <= deadline):
				student_letter.late_submission = True
				student_letter.save()
				log_custom_action(self.request.user, student_letter, ADDITION)
				messages.error(self.request, f'You are Starting an assessment at {current_time} which seems not within class time. The system has marked this as a Late submission. Please provide a reason')
			sections = Section.objects.filter(assessment_type__id=assessment_type_id)

			if sections.exists():
				for section in sections:
					student_section = StudentSection.objects.create(student_letter=student_letter, section=section)
					aspects = Aspect.objects.filter(Q(section=section) & Q(is_active=True))
					for aspect in aspects:
						StudentAspect.objects.create(student_section=student_section, aspect=aspect)
				messages.success(self.request, f'Added {student_letter.student} Successfully')
			else:
				student_name = student_letter.student.full_name
				student_letter.delete()
				location_instance.delete()
				messages.error(self.request, f'An error occured while creating the letter. Please try again')
				return redirect(f'{reverse_lazy("students_tp")}?search_query={student_name}')

			return redirect(reverse_lazy('edit_student_details', kwargs={'student_letter': student_letter.pk}))
		except MultipleObjectsReturned:
			location_instance.save()
			log_custom_action(self.request.user, location_instance, ADDITION)
			student_letter = StudentLetter.objects.create(student=student_instance, assessor=self.request.user, assessment_type=assessment_type, location=location_instance)
			log_custom_action(self.request.user, student_letter, ADDITION)
			sections = Section.objects.filter(assessment_type__id=assessment_type_id)
			if sections.exists():
				for section in sections:
					student_section = StudentSection.objects.create(student_letter=student_letter, section=section)
					aspects = Aspect.objects.filter(Q(section=section) & Q(is_active=True))
					for aspect in aspects:
						student_aspect = StudentAspect.objects.create(student_section=student_section, aspect=aspect)
				messages.success(self.request, f'Added {student_letter.student} Successfully')
			else:
				student_name = student_letter.student.full_name
				student_letter.delete()
				messages.error(self.request, f'An error occured while creating the letter. Please try again')
				return redirect(f'{reverse_lazy("students_tp")}?search_query={student_name}')

			return redirect(reverse_lazy('edit_student_details', kwargs={'student_letter': student_letter.pk}))
		except Exception as e:
			messages.error(self.request, f'Error: {e}')
			return redirect(f'{reverse_lazy("student_letters")}?search_query={student_instance.full_name}')
	
class PreviousAssessmentsView(LoginRequiredMixin, ListView):
	model = StudentLetter
	template_name = 'teaching_practice/previous_assessments.html'
	paginate_by = 10

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Previous Assessments'
		return context
	
	def get_queryset(self):
		get_request = self.request.GET
		student = self.kwargs.get('student')
		qs = StudentLetter.objects.filter(Q(to_delete=False) & Q(student__pk=student))
		search_query = get_request.get('search_query')
		if search_query:
			qs = qs.filter(Q(student__full_name__icontains=search_query) | Q(student__index__icontains=search_query))
		return qs.order_by('-created_at')
	
class PreviousAssessmentDetailView(LoginRequiredMixin, DetailView):
	model = StudentLetter
	template_name = 'teaching_practice/previous_assessment_detail.html'

	def get_object(self):
		return get_object_or_404(StudentLetter, pk=self.kwargs.get('pk'))

	def get_context_data(self, **kwargs):
		user = self.request.user
		assessment_types = AssessmentType.objects.all()
		admins = assessment_types.values_list('admins', flat=True)
		zonal_leaders = ZonalLeader.objects.all().values_list('assessor', flat=True)
		student_letter = self.get_object()
		student = student_letter.student
		sections = StudentSection.objects.prefetch_related('student_aspects').filter(student_letter=student_letter)
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = f'Previous {student.full_name} Assessments Detail'
		context['total'] = StudentLetter.objects.filter(Q(to_delete=False) & Q(student=student)).aggregate(total_score=Avg('total_score'))
		context['sections'] = sections
		context['letter'] = student_letter
		context['assessment_type'] = student_letter.assessment_type
		context['can_view_score'] = True if user.is_superuser or user in zonal_leaders or user.pk in admins else False
		return context
	
class AssessorAssessmentsListView(LoginRequiredMixin, AdminMixin, ListView):
	model = StudentLetter
	template_name  = 'teaching_practice/previous_assessments.html'
	paginate_by = 50

	def get_context_data(self, **kwargs):
		assessor = self.kwargs.get('assessor')		
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = f'{User.objects.get(pk=assessor).full_name}\'s Assessments'
		return context
	
	def get_queryset(self):
		assessor = self.kwargs.get('assessor')
		student_letters = StudentLetter.objects.filter(Q(to_delete=False) & Q(assessor__pk=assessor))
		return student_letters

class EditStudentLetterView(LoginRequiredMixin, ActivePeriodMixin, UpdateView):
	model = StudentLetter
	template_name = 'teaching_practice/update_student_letter.html'
	
	def get_success_url(self):
		student_letter_id = self.kwargs.get('pk')
		return reverse_lazy('pdf_report', kwargs={'pk': student_letter_id})
	
	def get_form_class(self):
		student_letter_id = self.kwargs.get('pk')
		student_letter_instance = StudentLetter.objects.get(pk=student_letter_id)
		if 'Diploma' in student_letter_instance.assessment_type.course.name:
			return UpdateDiplomaStudentLetter
		elif 'Certificate' in student_letter_instance.assessment_type.course.name:
			return UpdateCertificateStudentLetter
	
	def get_form_kwargs(self):
		kwargs = super(EditStudentLetterView, self).get_form_kwargs()
		kwargs['user'] = self.request.user
		return kwargs
	
	def form_valid(self, form):
		if form.is_valid():
			student_letter = self.get_object()
			sections = StudentSection.objects.filter(student_letter=student_letter)
			uncommented_sections = []
			student = student_letter.student
			null_fields = []
			for field in student._meta.get_fields():
				if isinstance(field, Field):
					value = getattr(student, field.name)
					if value is None and field.name not in ['created_by', 'period']:
						if 'Diploma' in student_letter.assessment_type.course.name:
							null_fields.append(field.name)
						elif 'Certificate' in student_letter.assessment_type.course.name:
							if field.name not in ['department']:
								null_fields.append(field.name)
			for field in student_letter._meta.get_fields():
				if isinstance(field, Field):
					value = getattr(student_letter, field.name)
					if value is None and field.name not in ['reason', 'to_delete', 'request_time', 'comments']:
						if 'Diploma' in student_letter.assessment_type.course.name:
							if field.name not in ['earc']:
								null_fields.append(field.name)
						elif 'Certificate' in student_letter.assessment_type.course.name:
							if field.name not in ['school', 'grade', 'learning_area', 'comments']:
								null_fields.append(field.name)

			for section in sections:
				if not section.comments:
					uncommented_sections.append(section.section)
			if len(uncommented_sections) > 0 or len(null_fields) > 0:
				messages.info(self.request, f'Please correct the following errors first')
				if len(null_fields) > 0:
					messages.info(self.request, f'Please fill in the following details for the student:')
					for field in null_fields:
						messages.error(self.request, field)
				if len(uncommented_sections) > 0:
					messages.info(self.request, f'Please fiil in the scores and comments for these sections:')
					for uncommented_section in uncommented_sections:
						messages.error(self.request, f'<a href="{reverse_lazy('edit_student_aspects', kwargs={'pk': uncommented_section.pk})}">{uncommented_section.name}</a>')
				return redirect(reverse_lazy('edit_student_letter', kwargs={'pk': student_letter.pk}))
			instance = form.save(commit=False)
			instance.is_editable = False
			instance.save()
			response = super().form_valid(form)
			return response
		
	def get_context_data(self, **kwargs):
		user = self.request.user
		student_letter_id = self.kwargs.get('pk')
		student_letter_instance = StudentLetter.objects.get(pk=student_letter_id)
		student_sections = StudentSection.objects.filter(student_letter=student_letter_instance)
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['location'] = student_letter_instance.location
		context['student'] = student_letter_instance.student
		context['title']= f'Update {student_letter_instance}\'s Letter'
		context['sections'] = student_sections
		context['letter'] = student_letter_instance
		context['can_edit'] = student_letter_instance.assessor == self.request.user or self.request.user.is_superuser
		return context
	
class EditStudentDetailsView(LoginRequiredMixin, ActivePeriodMixin, View):
	model = StudentLetter
	template_name = 'teaching_practice/student_details.html'
	
	def get_success_url(self):
		return reverse_lazy('edit_student_letter', kwargs={'pk': self.kwargs.get('pk')})
	
	def get(self, request, *args, **kwargs):
		student_letter_id = self.kwargs.get('student_letter')
		student_letter_instance = StudentLetter.objects.get(pk=student_letter_id)
		student_instance = student_letter_instance.student
		if 'Diploma' in student_letter_instance.assessment_type.course.name:
			student_form = DiplomaStudentForm(instance=student_instance)
			form = NewDiplomaStudentLetterForm(instance=student_letter_instance)
		elif 'Certificate' in student_letter_instance.assessment_type.course.name:
			student_form = CertificateStudentForm(instance=student_instance)
			form = NewCertificateStudentLetterForm(instance=student_letter_instance)
		context = {
			'student_form': student_form,
			'form': form,
			'is_nav_enabled': True,
			'title': f'Edit {student_letter_instance}\'s Details',
		}
		return render(request, 'teaching_practice/student_details.html', context=context)

	def post(self, request, *args, **kwargs):
		student_letter_id = self.kwargs.get('student_letter')
		student_letter_instance = StudentLetter.objects.get(pk=student_letter_id)
		student_instance = student_letter_instance.student
		
		if student_letter_instance.assessment_type.course.code == 'DSNE':
			post_letter_form = NewDiplomaStudentLetterForm(self.request.POST, instance=student_letter_instance)
			post_student_form = DiplomaStudentForm(self.request.POST, instance=student_instance)
			student_form = DiplomaStudentForm(instance=student_instance)
			letter_form = NewDiplomaStudentLetterForm(instance=student_letter_instance)
		elif student_letter_instance.assessment_type.course.code == 'CFA':
		# else:
			post_letter_form = NewCertificateStudentLetterForm(self.request.POST, instance=student_letter_instance)
			post_student_form = CertificateStudentForm(self.request.POST, instance=student_instance)
			student_form = CertificateStudentForm(instance=student_instance)
			letter_form = NewCertificateStudentLetterForm(instance=student_letter_instance)

		if post_letter_form.is_valid() and post_student_form.is_valid():

			letter = post_letter_form.save(commit=False)
			letter.save()

			student = post_student_form.save(commit=True)
			messages.success(self.request, f'Updated {student.full_name} Successfully')
			return redirect(reverse_lazy('edit_student_letter', kwargs={'pk': letter.pk}))
		else:
			context = {
				'student_form': post_student_form,
				'form': post_letter_form,
				'is_nav_enabled': True,
				'title': f'Edit {student_letter_instance}\'s Details',
			}
			return render(request, 'teaching_practice/student_details.html', context=context)
		
class PreviewStudentLetter(LoginRequiredMixin, DetailView):
	model = StudentLetter
	template_name = 'teaching_practice/previous_assessment_detail.html'

	def get_object(self):
		return get_object_or_404(StudentLetter, pk=self.kwargs.get('pk'))

	def get_context_data(self, **kwargs):
		user = self.request.user
		student_letter = self.get_object()
		student = student_letter.student
		sections = StudentSection.objects.prefetch_related('student_aspects').filter(student_letter=student_letter).order_by('section')
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = f'{student.full_name}\'s Assessment Preview'
		context['total'] = StudentLetter.objects.filter(Q(to_delete=False) & Q(student=student)).aggregate(total_score=Avg('total_score'))
		context['sections'] = sections
		context['letter'] = student_letter
		context['assessment_type'] = student_letter.assessment_type
		return context
	
class StudentAssessmentViewList(LoginRequiredMixin, ListView):
	model = StudentLetter
	template_name = 'teaching_practice/student_letters.html'
	context_object_name = 'studentletters'
	paginate_by = 50

	def get_context_data(self, **kwargs):
		user = self.request.user
		hods = Hod.objects.all().values_list('lecturer__user', flat=True)
		hod = None
		if user.pk in hods:
			hod = Hod.objects.get(lecturer__user=user)
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Student Assessments'
		context['search_query'] = SearchForm(self.request.GET)
		context['filter_form'] = FilterAssessmentsForm(self.request.GET, user=self.request.user)
		context['is_hod'] = True if user.is_superuser or user.pk in hods else False
		context['specialization'] = hod.department if hod else 'All Specializations'
		messages.info(self.request, 'These are the assessments that have been created. You can search for a specific assessment using the search bar below. If invalid, request for deletion.')
		return context
	
	def get_queryset(self):
		get_request = self.request.GET
		qs = StudentLetter.objects.prefetch_related('student_sections').filter(to_delete=False).annotate(search=SearchVector('student__full_name', 'student__index', 'school', 'grade', 'learning_area', 'zone', 'assessor__full_name'))
		user = self.request.user
		assessment_types = AssessmentType.objects.all()
		admins = assessment_types.values_list('admins', flat=True)
		if self.request.user.is_superuser:
			qs = qs
		elif user.pk in admins:
			admin_assessment_types = assessment_types.filter(admins=user)
			qs = qs.filter(assessment_type__in=admin_assessment_types)
		else:
			qs = qs.filter(Q(assessor=self.request.user))
		search_query = get_request.get('search_query')
		if department := get_request.get('department'):
			qs = qs.filter(Q(student__department=department))
		if specialization := get_request.get('specialization'):
			qs = qs.filter(Q(student__specialization=specialization))
		if zone := get_request.get('zone'):
			qs = qs.filter(Q(zone=zone))
		if assessment_type := get_request.get('assessment_type'):
			qs = qs.filter(Q(student_sections__section__assessment_type=assessment_type)).distinct()
		if assessor := get_request.get('assessor'):
			qs = qs.filter(Q(assessor__pk=assessor))
		if from_date := get_request.get('from_date'):
			if  from_time := get_request.get('from_time'):
				from_time = datetime.datetime.strptime(from_time, '%H:%M').time()
			else:
				from_time = datetime.time(00,00)
			timezone_aware_from_time = timezone.make_aware(datetime.datetime.combine(datetime.datetime.strptime(from_date, '%Y-%m-%d'), from_time))
			qs = qs.filter(created_at__gt=timezone_aware_from_time)
		if to_date := get_request.get('to_date'):
			if  to_time := get_request.get('to_time'):
				to_time = datetime.datetime.strptime(to_time, '%H:%M').time()
			else:
				to_time = datetime.time(00,00)
			timezone_aware_to_time = timezone.make_aware(datetime.datetime.combine(datetime.datetime.strptime(to_date, '%Y-%m-%d'), to_time))
			qs = qs.filter(created_at__lt=timezone_aware_to_time)
		if search_query:
			Query = SearchQuery(search_query)
			qs = qs.filter(search=Query)
		return qs.order_by('-created_at')
	
class InvalidStudentLetterViewList(LoginRequiredMixin, ListView):
	model = StudentLetter
	template_name = 'teaching_practice/invalid_student_letters.html'
	paginate_by = 50

	def get_context_data(self, **kwargs):
		students = Student.objects.filter(specialization__course__code='DSNE')
		invalid_students = []
		for student in students:
			if student.specialization and student.index:
				if len(student.index) != 11 or not str(student.index).startswith('TA'):
					invalid_students.append(student)
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Invalid Student Assessments'
		context['search_query'] = SearchForm(self.request.GET)
		context['filter_form'] = FilterAssessmentsForm(self.request.GET, user=self.request.user)
		context['invalid'] = invalid_students
		return context
	
	def get_queryset(self):
		get_request = self.request.GET
		if self.request.user.is_superuser:
			qs = StudentLetter.objects.prefetch_related('student_sections').filter(student_sections__section__assessment_type=None)
			
		search_query = get_request.get('search_query')
		if search_query:
			qs = qs.filter(Q(student__full_name__icontains=search_query) | Q(student__index__icontains=search_query) | Q(school__icontains=search_query) | Q(grade__icontains=search_query) | Q(learning_area__icontains=search_query) | Q(zone__icontains=search_query) | Q(assessor__full_name__icontains=search_query))
		return qs.order_by('student')
	
class IncompleteAssessmentsListView(LoginRequiredMixin, ListView):
	model = StudentLetter
	template_name = 'teaching_practice/invalid_student_letters.html'
	paginate_by = 50

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Incomplete Assessments'
		context['search_query'] = SearchForm(self.request.GET)
		context['filter_form'] = FilterAssessmentsForm(self.request.GET, user=self.request.user)
		messages.info(self.request, 'These are the assessments that have not been completed. Please complete them or request for their deletion.')
		return context
	
	def get_queryset(self):
		get_request = self.request.GET
		user = self.request.user
		letters = StudentLetter.objects.prefetch_related('student_sections').filter(Q(to_delete=False) & (Q(comments=None) | Q(total_score=0)))
		assessment_types = AssessmentType.objects.all()
		admins = assessment_types.values_list('admins', flat=True)
		if user.is_superuser:
			qs = letters
		elif user.id in admins:
			admin_assessment_types = assessment_types.filter(admins=user)
			qs = letters.filter(assessment_type__in=admin_assessment_types)
		else:
			qs = letters.filter(assessor=self.request.user)
		if department := get_request.get('department'):
			qs = qs.filter(Q(student__department=department))
		if specialization := get_request.get('specialization'):
			qs = qs.filter(Q(student__specialization=specialization))
		if zone := get_request.get('zone'):
			qs = qs.filter(Q(zone=zone))
		if assessment_type := get_request.get('assessment_type'):
			qs = qs.filter(Q(student_sections__section__assessment_type=assessment_type)).distinct()
		if assessor := get_request.get('assessor'):
			qs = qs.filter(Q(assessor__pk=assessor))
		if from_date := get_request.get('from_date'):
			if  from_time := get_request.get('from_time'):
				from_time = datetime.datetime.strptime(from_time, '%H:%M').time()
			else:
				from_time = datetime.time(00,00)
			timezone_aware_from_time = timezone.make_aware(datetime.datetime.combine(datetime.datetime.strptime(from_date, '%Y-%m-%d'), from_time))
			qs = qs.filter(created_at__gt=timezone_aware_from_time)
		if to_date := get_request.get('to_date'):
			if  to_time := get_request.get('to_time'):
				to_time = datetime.datetime.strptime(to_time, '%H:%M').time()
			else:
				to_time = datetime.time(00,00)
			timezone_aware_to_time = timezone.make_aware(datetime.datetime.combine(datetime.datetime.strptime(to_date, '%Y-%m-%d'), to_time))
			qs = qs.filter(created_at__lt=timezone_aware_to_time)	
		search_query = get_request.get('search_query')
		if search_query:
			qs = qs.filter(Q(student__full_name__icontains=search_query) | Q(student__index__icontains=search_query) | Q(school__icontains=search_query) | Q(grade__icontains=search_query) | Q(learning_area__icontains=search_query) | Q(zone__icontains=search_query) | Q(assessor__full_name__icontains=search_query))
		return qs.order_by('student')

class DeleteStudentLetterView(LoginRequiredMixin, AdminMixin, View):
	def post(self, request, letter_id, *args, **kwargs):
		letter = StudentLetter.objects.get(pk=letter_id)
		letter.delete()
		log_custom_action(request.user, letter, DELETION)
		messages.success(request, f'Deleted the Student Assessment {letter.student.full_name}')
		return redirect(reverse_lazy('pending_deletion'))
		
class RequestDeletionView(LoginRequiredMixin, View):
	def post(self, *args, **kwargs):
		obj_id = self.kwargs.get('pk')
		path = self.kwargs.get('path')
		letter = StudentLetter.objects.get(pk=obj_id)
		letter.to_delete = True
		letter.request_time = timezone.now()
		letter.save()
		request_deletion(self.request, obj_id, path)
		messages.success(self.request, 'Your request for deletion has been sent successfully. The admin will review it and take action if necessary.')
		return redirect(reverse_lazy('pending_deletion'))
	
class PendingDeletionView(LoginRequiredMixin, ListView):
	model = StudentLetter
	template_name = 'teaching_practice/invalid_student_letters.html'
	paginate_by = 50

	def get_queryset(self):
		user = self.request.user
		qs = StudentLetter.objects.filter(to_delete=True)
		if user.is_superuser:
			qs = qs
		else:
			qs = qs.filter(assessor=user)
		return qs

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Pending Deletion'
		context['filter_form'] = FilterAssessmentsForm(self.request.GET, user=self.request.user)
		return context
	
class CancelDeletionView(LoginRequiredMixin, View):
	def post(self, *args, **kwargs):
		obj_id = self.kwargs.get('pk')
		path = self.kwargs.get('path')
		letter = StudentLetter.objects.get(pk=obj_id)
		letter.to_delete = False
		letter.request_time = timezone.now()
		letter.save()
		request_deletion(self.request, obj_id, path)
		messages.success(self.request, 'The request for deletion has been cancelled successfully.')
		return redirect(f"{reverse_lazy('student_letters')}?search_query={letter.pk}")

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

class EditStudentSectionView(LoginRequiredMixin, ActivePeriodMixin, UpdateView):
	model = StudentSection
	form_class = UpdateStudentSection
	template_name = 'teaching_practice/student_section_scores.html'

	def get_success_url(self):
		student_section = self.kwargs.get('pk')
		student_letter_id = StudentSection.objects.get(pk=student_section).student_letter.pk
		return reverse_lazy('edit_student_letter', kwargs={'pk': student_letter_id})

	def get_context_data(self, **kwargs):
		user = self.request.user
		student_section = self.kwargs.get('pk')
		section = StudentSection.objects.get(pk=student_section)
		student_aspects = StudentAspect.objects.filter(student_section=student_section)
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = f'{section.section.name} Scores'
		context['aspects'] = student_aspects
		context['section'] = section
		context['pk'] = student_section
		context['can_edit'] = section.student_letter.assessor == self.request.user
		context['is_editable'] = section.student_letter.is_editable
		return context
	
	def form_valid(self, form):
		form = self.get_form(self.get_form_class())
		student_section = self.kwargs.get('pk')
		student_letter = StudentSection.objects.get(pk=student_section).student_letter
		student_sections = StudentSection.objects.filter(student_letter=student_letter)		
		score =0
		if student_letter.is_editable:
			for section in student_sections:
				score += section.score
			if student_letter.assessment_type.short_name == 'CFA':
				student_letter.total_score = (score / 92) * 100
			else:
				student_letter.total_score = score
			student_letter.save()

			response = super().form_valid(form)
			if "save_continue" in self.request.POST:
				student_section = StudentSection.objects.get(pk=student_section)
				current_number = student_section.section.number
				student_letter = student_section.student_letter
				last_number = Section.objects.filter(assessment_type=student_section.section.assessment_type).count()
				if current_number != last_number:
					next_number = current_number + 1
					next_section = StudentSection.objects.get(Q(section__number=next_number) & Q(student_letter=student_letter)).pk
					return redirect(reverse_lazy('edit_student_aspects', kwargs={'pk': next_section}))
			return response
		else:
			raise PermissionDenied("You do not have permission to edit this section.")

class StudentSectionsViewList(LoginRequiredMixin, ActivePeriodMixin, ListView):
	model = StudentSection
	template_name = 'teaching_practice/student_sections.html'
	context_object_name = 'studentsections'
	paginate_by = 50

	def get_queryset(self):
		get_request = self.request.GET
		qs = StudentSection.objects.all()
		search_query = get_request.get('search_query')
		if search_query:
			qs = qs.filter(Q(student__full_name__icontains=search_query) | Q(student__index__icontains=search_query) | Q(section__name__icontains=search_query))
		return qs.order_by('student')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['search_query'] = SearchForm(self.request.GET)
		return context

class EditStudentAspectView(LoginRequiredMixin, ActivePeriodMixin, View):
	model = StudentAspect
	template_name = 'teaching_practice/add_aspect_scores.html'
	
	def get_success_url(self):
		return reverse_lazy('edit_student_section', kwargs={'pk': self.kwargs.get('pk')})

	def get(self, request, *args, **kwargs):
		student_section_id = self.kwargs.get('pk')
		student_section = get_object_or_404(StudentSection, pk=student_section_id)
		student_letter = student_section.student_letter

		queryset = StudentAspect.objects.filter(student_section=student_section)
		formset = StudentAspectFormSet(queryset=queryset)

		context = {
			'is_nav_enabled': True,
			'title': 'Add Aspect Scores',
			'section': student_section,
			'letter': student_letter,
			'formset': formset,
			'can_edit': student_letter.assessor == self.request.user,
		}

		return render(request, self.template_name, context)

	def post(self, request, *args, **kwargs):
		student_section_id = self.kwargs.get('pk')
		student_section = get_object_or_404(StudentSection, pk=student_section_id)
		student_letter = student_section.student_letter

		queryset = StudentAspect.objects.filter(student_section=student_section)
		formset = StudentAspectFormSet(request.POST, queryset=queryset)

		context = {
			'is_nav_enabled': True,
			'title': 'Add Aspect Scores',
			'section': student_section,
			'letter': student_letter,
			'formset': formset,
			'can_edit': student_letter.assessor == self.request.user,
		}

		if formset.is_valid():
			errors = []
			if student_letter.assessor == self.request.user and student_letter.is_editable:
				for form in formset:
					if form.cleaned_data:
						score = form.cleaned_data.get('score')
						aspect = form.cleaned_data.get('aspect')
						threshold = Aspect.objects.get(pk=aspect.pk).contribution
						
						if score > threshold:
							errors.append(f"'{aspect.name}' score of '{score}' exceeds the maximum ({threshold})")
						if score < 0:
							errors.append(f"'{aspect.name}' score of '{score}' cannot be negative")

				if len(errors) == 0:
					formset.save()
					student_aspects = StudentAspect.objects.filter(student_section=student_section)
					sum = 0
					for aspect in student_aspects:
						sum += aspect.score
					student_section.score = sum
					student_section.save()
					return redirect(self.get_success_url())
				
				else:
					context['errors']= errors
					return render(request, self.template_name, context)
			else:
				messages.error(request, 'You do not have permission to edit this')

		return render(request, self.template_name, context)

class StudentAspectsViewList(LoginRequiredMixin, ListView):
	model = StudentAspect
	template_name = 'teaching_practice/student_aspects.html'
	context_object_name = 'studentaspects'
	paginate_by = 50

	def get_queryset(self):
		get_request = self.request.GET
		qs  = StudentAspect.objects.all()
		search_query = get_request.get('search_query')
		if search_query:
			qs = qs.filter(Q(student__full_name__icontains=search_query) | Q(student__index__icontains=search_query) | Q(aspect__name__icontains=search_query) | Q(aspect__section__name__icontains=search_query))
		return qs.order_by('student')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['search_query'] = SearchForm(self.request.GET)
		return context

class GeneratePDF(LoginRequiredMixin, WeasyTemplateResponseMixin, DetailView):
	model = StudentLetter
	# template_name = 'teaching_practice/general_pdf_report.html'

	def get_object(self):
		return get_object_or_404(StudentLetter, pk=self.kwargs.get('pk'))
	
	def get_template_names(self):
		student_letter = self.get_object()
		assessment_type = student_letter.assessment_type
		if 'Diploma' in assessment_type.course.name:
			return ['teaching_practice/diploma_pdf_report.html']
		elif 'Certificate' in assessment_type.course.name:
			return ['teaching_practice/certificate_pdf_report.html']
		return super().get_template_names()
	
	def get_pdf_filename(self):
		student = StudentLetter.objects.get(pk=self.kwargs.get('pk')).student
		return f'{student.full_name}.pdf'

	def get_context_data(self, **kwargs):
		letter = self.get_object()
		context = super().get_context_data(**kwargs)
		sections = StudentSection.objects.prefetch_related('student_aspects').filter(student_letter=letter)
		aspects = StudentAspect.objects.filter(student_section__student_letter=letter)
		image_url = self.request.build_absolute_uri(settings.MEDIA_URL + 'icons/kise_logo.png')
		context['is_nav_enabled'] = True
		context["title"] = f'{letter.student.full_name}\'s Assessment Report'
		context['letter'] = letter
		context['sections'] = sections
		context['aspects'] = aspects
		context['image_url'] = image_url
		context['heading'] = letter.assessment_type.name
		return context
	
	def render_to_response(self, context, **response_kwargs):
		response = super().render_to_response(context, **response_kwargs)

		response.render()

		with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmpfile:
			tmpfile.write(response.content)
			tmpfile.seek(0)
		
		report_type = self.kwargs.get('type')
		if report_type != 'regenerate':
			send_student_report(self.request, tmpfile.name, self.get_object())

		return response
	
class ZonesViewList(LoginRequiredMixin, AdminHeadMixin, ListView):
	model = StudentLetter
	template_name = 'teaching_practice/zonal_leader.html'
	context_object_name = 'studentletters'
	paginate_by = 50

	def get_queryset(self):
		get_request = self.request.GET
		user = self.request.user
		zonal_leaders = ZonalLeader.objects.all().values_list('assessor__pk', flat=True)
		qs = StudentLetter.objects.filter(Q(to_delete=False) | Q(is_editable=True))
		assessment_types = AssessmentType.objects.all()
		admins = assessment_types.values_list('admins', flat=True)
		if user.is_superuser:
			qs = qs
		if user.id in admins:
			admin_assessment_types = assessment_types.filter(admins=user)
			qs = qs.filter(assessment_type__in=admin_assessment_types)
		elif user.pk in zonal_leaders:
			zone = ZonalLeader.objects.get(assessor=user)
			qs = qs.filter(zone=zone)
		else:
			raise PermissionDenied
		if department := get_request.get('department'):
			qs = qs.filter(Q(student__department=department))
		if specialization := get_request.get('specialization'):
			qs = qs.filter(Q(student__specialization=specialization))
		if zone := get_request.get('zone'):
			qs = qs.filter(Q(zone=zone))
		if assessment_type := get_request.get('assessment_type'):
			qs = qs.filter(Q(student_sections__section__assessment_type=assessment_type)).distinct()
		if assessor := get_request.get('assessor'):
			qs = qs.filter(Q(assessor__pk=assessor))
		if from_date := get_request.get('from_date'):
			if  from_time := get_request.get('from_time'):
				from_time = datetime.datetime.strptime(from_time, '%H:%M').time()
			else:
				from_time = datetime.time(00,00)
			timezone_aware_from_time = timezone.make_aware(datetime.datetime.combine(datetime.datetime.strptime(from_date, '%Y-%m-%d'), from_time))
			qs = qs.filter(created_at__gt=timezone_aware_from_time)
		if to_date := get_request.get('to_date'):
			if  to_time := get_request.get('to_time'):
				to_time = datetime.datetime.strptime(to_time, '%H:%M').time()
			else:
				to_time = datetime.time(00,00)
			timezone_aware_to_time = timezone.make_aware(datetime.datetime.combine(datetime.datetime.strptime(to_date, '%Y-%m-%d'), to_time))
			qs = qs.filter(created_at__lt=timezone_aware_to_time)
		search_query = get_request.get('search_query')
		if search_query:
			qs = qs.filter(Q(student__full_name__icontains=search_query) | Q(student__index__icontains=search_query) | Q(school__icontains=search_query) | Q(grade__icontains=search_query) | Q(learning_area__icontains=search_query))
		return qs.order_by('student')

	def get_context_data(self, **kwargs):
		user = self.request.user
		zone = ZonalLeader.objects.filter(assessor=user).first()
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Zonal Leader'
		context['search_query'] = SearchForm(self.request.GET)
		context['filter_form'] = FilterAssessmentsForm(self.request.GET, user=self.request.user)
		context['zone'] = zone
		return context
	
class ZonalLeaderViewList(LoginRequiredMixin, CreateView):
	model = ZonalLeader
	template_name = 'teaching_practice/zonal_leaders.html'
	form_class = ZonalLeaderForm
	success_url = reverse_lazy('zonal_leaders')
	
	def get_context_data(self, **kwargs):
		objs = Student.objects.all()
		for obj in objs:
			assessment = StudentLetter.objects.filter(student=obj).order_by('created_at', 'zone').first()
			for letter in StudentLetter.objects.filter(student=obj):
				letter.zone = assessment.zone
				letter.save()
		user = self.request.user
		zonal_leaders = ZonalLeader.objects.all().values_list('assessor', flat=True)
		assessment_types = AssessmentType.objects.all()
		admins = assessment_types.values_list('admins', flat=True)
		context = super().get_context_data(**kwargs)
		if user.is_superuser or user.id in admins:
			context['zonal_leaders'] = ZonalLeader.objects.all()
		elif user in zonal_leaders:
			zone = ZonalLeader.objects.get(assessor=user)
			context['zonal_leaders'] = ZonalLeader.objects.filter(zone=zone)
		else:
			context['zonal_leaders'] = ZonalLeader.objects.none()
		context['is_nav_enabled'] = True
		context['title'] = 'Zonal Leaders'
		return context

class DeleteObject(LoginRequiredMixin, DeleteView):
	model = Aspect
	success_url = reverse_lazy('aspects')
	template_name = 'teaching_practice/aspect_confirm_delete.html'

	def get_object(self, queryset = None):
		
		return super().get_object(queryset)
	
	def post(self, request, *args, **kwargs):
		model = self.request.POST.get('model')
		obj_pk = self.request.POST.get('pk')
		obj = get_object_or_404(model, obj_pk)
		obj.delete()
		return redirect(self.get_success_url())
	
class ExportAssessmentPreview(LoginRequiredMixin, ListView):
	model = StudentLetter
	template_name = 'teaching_practice/export_assessments_preview.html'
	paginate_by = 50

	def get_queryset(self):
		user = self.request.user
		queryset = StudentLetter.objects.exclude(Q(comments=None) | Q(total_score=0) | Q(to_delete=True ) | Q(is_editable=True))
		assessment_types = AssessmentType.objects.all()
		admins = assessment_types.values_list('admins', flat=True)
		zonal_leader = ZonalLeader.objects.filter(assessor=user).first()
		hod = Hod.objects.filter(lecturer__user=user).first()
		if user.is_superuser:
			assessments = queryset.order_by('created_at', 'zone')
		elif user.pk in admins:
			admin_assessment_types = assessment_types.filter(admins=user)
			assessments = queryset.filter(assessment_type__in=admin_assessment_types)
		elif zonal_leader:
			zone = zonal_leader.zone_name
			assessments = queryset.filter(zone=zone).order_by('created_at')
		elif hod:
			specialization = hod.department
			assessments = queryset.filter(student__specialization=specialization).order_by('created_at', 'zone')
		else:
			assessments = queryset.filter(assessor=user).order_by('created_at', 'zone')

		return assessments

	def get_context_data(self, **kwargs) :
		user = self.request.user
		assessment_types = AssessmentType.objects.all()
		admins = assessment_types.values_list('admins', flat=True)
		zonal_leader = ZonalLeader.objects.filter(assessor=user).first()
		hod = Hod.objects.filter(lecturer__user=user).first()
		if user.is_superuser:
			name = 'All Specializations Assessments'
		elif user.pk in admins:
			admin_assessment_types = assessment_types.filter(admins=user)
			names = ''
			for assessment in admin_assessment_types:
				names += f'{str(assessment.short_name)}, '
			name = f'{names.strip()} Assessments'
		elif zonal_leader:
			zone = zonal_leader.zone_name
			name = f'{zone} Assessments'
		elif hod:
			specialization = hod.department
			name = f'{specialization.name} Assessments'
		else:
			name = f'{(user.full_name).capitalize()} Assessments'
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = f'Export {name}'
		context['name'] = name
		return context
	
class ExportAssessmentReport(LoginRequiredMixin, View):
	def get(self, request):
		user = self.request.user
		queryset = StudentLetter.objects.exclude(Q(comments=None) | Q(total_score=0) | Q(to_delete=True ) | Q(is_editable=True))
		assessment_types = AssessmentType.objects.all()
		admins = assessment_types.values_list('admins', flat=True)
		zonal_leader = ZonalLeader.objects.filter(assessor=user).first()
		hod = Hod.objects.filter(lecturer__user=user).first()
		if user.is_superuser:
			assessments = queryset.order_by('created_at', 'zone')
			name = 'All Specializations Assessments'
		elif user.pk in admins:
			admin_assessment_types = assessment_types.filter(admins=user)
			assessments = queryset.filter(assessment_type__in=admin_assessment_types)
			names = ''
			for assessment in assessment_types:
				names += f'{str(assessment.short_name)} '
			name = f'{names.strip()} Assessments'
		elif zonal_leader:
			zone = zonal_leader.zone_name
			assessments = queryset.filter(zone=zone).order_by('created_at')
			name = f'{zone} Assessments'
		elif hod:
			specialization = hod.department
			assessments = queryset.filter(student__specialization=specialization).order_by('created_at', 'zone')
			name = f'{specialization.name} Assessments'
		else:
			assessments = queryset.filter(assessor=user).order_by('created_at', 'zone')
			name = f'{(user.fullname).capitalize()} Assessments'
		grouped = defaultdict(list)
		
		# Group values by name
		for obj in assessments:
			grouped[obj.student.full_name, obj.student.index, obj.zone].append((obj.total_score, obj.assessment_type.name, obj.assessor.full_name, obj.created_at.astimezone().strftime('%Y-%m-%d %I:%M:%S %p')))

		# Determine the max number of values per name to set column headers
		max_items = max(len(values) for values in grouped.values())

		# Column headers
		headers = ['Name', 'Assessment No.', 'Zone']
		for i in range(max_items):
			headers.extend([f'Assessment {i+1}', f'Assessment {i+1} Type', f'Assessment {i+1} Assessor', f'Assessment {i+1} Date & Time'])

		# Prepare the response
		response = HttpResponse(content_type='text/csv')
		response['Content-Disposition'] = f'attachment; filename="{name}.csv"'
		writer = csv.writer(response)
		writer.writerow(headers)

		# Write rows
		for (name, index, zone), values in grouped.items():
			row = [name, index, zone]
			for score, assessment_type, assessor, created_at in values:
				row.extend([score, assessment_type, assessor, created_at])

			missing = max_items - len(values)
			row.extend(['', ''] * missing)
			writer.writerow(row)

		return response

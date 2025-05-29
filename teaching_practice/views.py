import datetime
from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned, PermissionDenied
from django.shortcuts import get_object_or_404, render, redirect
from dal import autocomplete
from django.template.context_processors import media
from django.utils import timezone
from django.views.generic.base import View
from django.urls import reverse_lazy
from dev.forms import CustomUserCreationForm
from dev.models import User
from teaching_practice.mailer import request_deletion, send_student_report
from teaching_practice.mixins import ActivePeriodMixin, AdminMixin
from .forms import FilterAssessmentsForm, NewAspect, NewLocationForm, NewSection, NewStudentAspect, NewStudentForm, NewStudentLetter, NewStudentSection, NewSubSection, PeriodForm, SearchForm, StudentForm, UpdateAspect, UpdateSection, UpdateStudentAspect, UpdateStudentLetter, UpdateStudentSection, StudentAspectFormSet, UpdateSubSection, ZonalLeaderForm
from .models import Period, Student, Section, StudentAspect, StudentLetter, StudentSection, Aspect, Location, SubSection, ZonalLeader
from django.views.generic import ListView, CreateView, FormView, UpdateView, DeleteView, DetailView
from django.db.models import Q, Avg, F, Count, ExpressionWrapper, FloatField, Value
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
		qs = User.objects.filter(Q(role='lecturer') & Q(is_active=True))
		if search_query := self.request.GET.get('search_query'):
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
		students = Student.objects.exclude(full_name__icontains='test')
		if user.is_staff:
			initiated_assessments = StudentLetter.objects.all()
		else:
			if user.pk in zonal_leaders:
				initiated_assessments = StudentLetter.objects.filter(assessor=user)
			else:
				initiated_assessments = StudentLetter.objects.filter(assessor=user)

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
		qs = Section.objects.all()
		search_query = self.request.GET.get('search_query')
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
		qs = SubSection.objects.all()
		search_query = self.request.GET.get('search_query')
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
		return context
	
	def get_queryset(self):
		qs = Aspect.objects.all()
		search_query = self.request.GET.get('search_query')
		if search_query:
			qs = qs.filter(Q(name__icontains=search_query) | Q(section__name__icontains=search_query))
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
		if form.is_valid:
			instance = form.save(commit=False)
			instance.created_by = self.request.user
			active_period=Period.objects.get(is_active=True)
			instance.period = active_period
			students = Student.objects.filter(period=active_period).exclude(full_name__icontains='test')
			student_numbers = students.values_list('index', flat=True)
			student_names = students.values_list('full_name', flat=True)
			if (instance.index).strip(' ') in student_numbers:
				student = Student.objects.get(Q(index=instance.index) & Q(period=active_period))
				messages.error(self.request, f'{instance.full_name} already exists')
				return redirect(f'{reverse_lazy("students_tp")}?search_query={student.index}')
			else:
				instance.save()
				log_custom_action(self.request.user, instance, ADDITION)
				self.object = instance
				messages.success(self.request, f'Added {instance.full_name} Successfully')
				return redirect(f'{reverse_lazy('students_tp')}?search_query={instance.index}')
		else:
			return self.form_invalid(form)
	
class EditStudentView(LoginRequiredMixin, ActivePeriodMixin, UpdateView):
	model = Student
	form_class = StudentForm
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
		user = self.request.user
		searched = self.request.GET.get('search_query')
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Students'
		context['search_query'] = SearchForm(self.request.GET)
		context['location_form'] = NewLocationForm(self.request.POST)
		context['searched'] = True if searched else False
		return context
	
	def get_queryset(self):
		active_period = Period.objects.get(is_active=True)
		qs = Student.objects.filter(period=active_period)
		search_query = self.request.GET.get('search_query')
		if search_query:
			qs = qs.filter(Q(full_name__icontains=search_query) | Q(index__icontains=search_query.strip(' ')) | Q(email__icontains=search_query))
		if filter_query := self.request.GET.get('filter_query'):
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
		assessment_type = self.kwargs.get('assessment_type')
		deadline = timezone.datetime.strptime('17:00', '%H:%M').time()
		start_time = timezone.datetime.strptime('08:00', '%H:%M').time()
		current_time = timezone.datetime.now().astimezone().time()

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
				assessor=self.request.user, defaults={'location':location_instance})
			if not created:
				previous_assessment_type = StudentSection.objects.filter(student_letter=student_letter).first().section.assessment_type
				creation_time = student_letter.created_at
				time_difference = timezone.now() - creation_time
				if time_difference.days < 7 and assessment_type == previous_assessment_type:
					return redirect(reverse_lazy('edit_student_letter', kwargs={'pk': student_letter.pk}))
				else:
					student_letter = StudentLetter.objects.create(student=student_instance, assessor=self.request.user, location=location_instance)
					log_custom_action(self.request.user, student_letter, ADDITION)
					
			location_instance.save()
			log_custom_action(self.request.user, location_instance, ADDITION)
			if not (current_time > start_time <= current_time <= deadline):
				student_letter.late_submission = True
				student_letter.save()
				log_custom_action(self.request.user, student_letter, ADDITION)
				messages.error(self.request, f'You are Starting an assessment at {current_time} which seems not within class time. The system has marked this as a Late submission. Please provide a reason')
				# return redirect(f'{reverse_lazy("edit_student_details", kwargs={'student_letter': student_letter.pk})}')
			messages.success(self.request, f'Location Created Successfully')
			if assessment_type == 'General':
				sections = Section.objects.filter(assessment_type='General')
			elif assessment_type == 'PHE':
				sections = Section.objects.filter(assessment_type='PHE')
			else:
				raise Http404('Invalid Assessment Type')

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
		except MultipleObjectsReturned:
			messages.error(self.request, f'The Assessment already exist pick it from ones below')
			return redirect(f'{reverse_lazy("student_letters")}?search_query={student_instance.full_name}')
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
		student = self.kwargs.get('student')
		qs = StudentLetter.objects.filter(student__pk=student)
		search_query = self.request.GET.get('search_query')
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
		student_letter = self.get_object()
		student = student_letter.student
		sections = StudentSection.objects.prefetch_related('student_aspects').filter(student_letter=student_letter)
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = f'Previous {student.full_name} Assessments Detail'
		context['total'] = StudentLetter.objects.filter(student=student).aggregate(total_score=Avg('total_score'))
		context['sections'] = sections
		context['letter'] = student_letter
		context['assessment_type'] = StudentSection.objects.filter(student_letter=student_letter).first().section.assessment_type
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
		student_letters = StudentLetter.objects.filter(assessor=assessor)
		return student_letters

class EditStudentLetterView(LoginRequiredMixin, ActivePeriodMixin, UpdateView):
	model = StudentLetter
	form_class = UpdateStudentLetter
	template_name = 'teaching_practice/update_student_letter.html'
	
	def get_success_url(self):
		student_letter_id = self.kwargs.get('pk')
		return reverse_lazy('pdf_report', kwargs={'pk': student_letter_id})
	
	def get_form_kwargs(self):
		kwargs = super(EditStudentLetterView, self).get_form_kwargs()
		kwargs['user'] = self.request.user
		return kwargs
	
	def form_valid(self, form):
		if form.is_valid():
			response = super().form_valid(form)
			student_letter = self.get_object()
			sections = StudentSection.objects.filter(student_letter=student_letter)
			uncommented_sections = []
			student = student_letter.student
			null_fields = []
			for field in student._meta.get_fields():
				if isinstance(field, Field):
					value = getattr(student, field.name)
					if value is None and field.name not in ['created_by', 'period']:
						null_fields.append(field.name)
			for field in student_letter._meta.get_fields():
				if isinstance(field, Field):
					value = getattr(student_letter, field.name)
					if value is None and field.name != 'reason':
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
					messages.info(self.request, f'Please fiil in the grades and comments for these sections:')
					for uncommented_section in uncommented_sections:
						messages.error(self.request, f'<a href="{reverse_lazy('edit_student_aspects', kwargs={'pk': uncommented_section.pk})}">{uncommented_section.name}</a>')
				return redirect(reverse_lazy('edit_student_letter', kwargs={'pk': student_letter.pk}))
			return response
		
	def get_context_data(self, **kwargs):
		user = self.request.user
		student_letter_id = self.kwargs.get('pk')
		student_letter_instance = StudentLetter.objects.get(pk=student_letter_id)
		student_sections = StudentSection.objects.filter(student_letter=student_letter_instance)
		student_aspects = StudentAspect.objects.filter()
		aspects = Aspect.objects.all()
		sections = Section.objects.all()
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['location'] = student_letter_instance.location
		context['student'] = student_letter_instance.student
		context['title']= f'Update {student_letter_instance}\'s Letter'
		context['sections'] = student_sections
		context['letter'] = student_letter_instance
		context['can_edit'] = student_letter_instance.assessor == self.request.user
		return context
	
class EditStudentDetailsView(LoginRequiredMixin, ActivePeriodMixin, View):
	model = StudentLetter
	form_class = NewStudentLetter
	template_name = 'teaching_practice/student_details.html'
	
	def get_success_url(self):
		return reverse_lazy('edit_student_letter', kwargs={'pk': self.kwargs.get('pk')})
	
	def get(self, request, *args, **kwargs):
		student_letter_id = self.kwargs.get('student_letter')
		student_letter_instance = StudentLetter.objects.get(pk=student_letter_id)
		student_instance = student_letter_instance.student
		context = {
			'student_form': StudentForm(instance=student_instance),
			'form': NewStudentLetter(instance=student_letter_instance),
			'is_nav_enabled': True,
			'title': f'Edit {student_letter_instance}\'s Details',
		}
		return render(request, 'teaching_practice/student_details.html', context=context)

	def post(self, request, *args, **kwargs):
		student_letter_id = self.kwargs.get('student_letter')
		student_letter_instance = StudentLetter.objects.get(pk=student_letter_id)
		student_instance = student_letter_instance.student
		letter_form = NewStudentLetter(self.request.POST, instance=student_letter_instance)
		student_form = StudentForm(self.request.POST, instance=student_instance)

		if letter_form.is_valid() and student_form.is_valid():
			letter = letter_form.save(commit=False)
			if letter.late_submission and letter.reason is None:
				messages.error(self.request, f'Please provide a reason for late submission')
				return redirect(reverse_lazy('edit_student_details'), kwargs={'student_letter': letter.pk})
			else:
				letter.save()

				student = student_form.save(commit=True)
				messages.success(self.request, f'Updated {student.full_name} Successfully')
				return redirect(reverse_lazy('edit_student_letter', kwargs={'pk': letter.pk}))
		else:
			context = {
				'student_form': StudentForm(instance=student_instance),
				'form': NewStudentLetter(instance=student_letter_instance),
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
		context['total'] = StudentLetter.objects.filter(student=student).aggregate(total_score=Avg('total_score'))
		context['sections'] = sections
		context['letter'] = student_letter
		context['assessment_type'] = StudentSection.objects.filter(student_letter=student_letter).first().section.assessment_type
		return context
	
class StudentLetterViewList(LoginRequiredMixin, ListView):
	model = StudentLetter
	template_name = 'teaching_practice/student_letters.html'
	context_object_name = 'studentletters'
	paginate_by = 50

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Student Letters'
		context['search_query'] = SearchForm(self.request.GET)
		context['filter_form'] = FilterAssessmentsForm(self.request.GET, user=self.request.user)
		return context
	
	def get_queryset(self):
		if self.request.user.is_staff:
			qs = StudentLetter.objects.prefetch_related('student_sections').all()
		else:
			qs = StudentLetter.objects.prefetch_related('student_sections').filter(assessor=self.request.user)
		search_query = self.request.GET.get('search_query')
		if department := self.request.GET.get('department'):
			qs = qs.filter(Q(student__department=department))
		if specialization := self.request.GET.get('specialization'):
			qs = qs.filter(Q(student__specialization=specialization))
		if zone := self.request.GET.get('zone'):
			qs = qs.filter(Q(zone=zone))
		if assessment_type := self.request.GET.get('assessment_type'):
			qs = qs.filter(Q(student_sections__section__assessment_type=assessment_type)).distinct()
		if assessor := self.request.GET.get('assessor'):
			qs = qs.filter(Q(assessor__pk=assessor))
		if from_date := self.request.GET.get('from_date'):
			if  from_time := self.request.GET.get('from_time'):
				from_time = datetime.time(from_time)
			else:
				from_time = datetime.time(00,00)
			timezone_aware_from_time = timezone.make_aware(datetime.datetime.combine(datetime.datetime.strptime(from_date, '%Y-%m-%d'), from_time))
			qs = qs.filter(created_at__gt=timezone_aware_from_time)
		if to_date := self.request.GET.get('to_date'):
			if  to_time := self.request.GET.get('to_time'):
				to_time = datetime.time(to_time)
			else:
				to_time = datetime.time(00,00)
			timezone_aware_to_time = timezone.make_aware(datetime.datetime.combine(datetime.datetime.strptime(to_date, '%Y-%m-%d'), to_time))
			qs = qs.filter(created_at__lt=timezone_aware_to_time)
		if search_query:
			qs = qs.filter(Q(pk__icontains=search_query) | Q(student__full_name__icontains=search_query) | Q(student__index__icontains=search_query) | Q(school__icontains=search_query) | Q(grade__icontains=search_query) | Q(learning_area__icontains=search_query) | Q(zone__icontains=search_query) | Q(assessor__full_name__icontains=search_query))
		return qs.order_by('-created_at')
	
class InvalidStudentLetterViewList(LoginRequiredMixin, ListView):
	model = StudentLetter
	template_name = 'teaching_practice/invalid_student_letters.html'
	paginate_by = 50

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Invalid Student Letters'
		context['search_query'] = SearchForm(self.request.GET)
		return context
	
	def get_queryset(self):
		if self.request.user.is_superuser:
			qs = StudentLetter.objects.prefetch_related('student_sections').filter(student_sections__section__assessment_type=None)
			
		search_query = self.request.GET.get('search_query')
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
		return context
	
	def get_queryset(self):
		letters = StudentLetter.objects.prefetch_related('student_sections').filter(Q(comments=None) | Q(total_score=0)).exclude(student__full_name__icontains='test')
		if self.request.user.is_staff:
			qs = letters
		else:
			qs = letters.filter(assessor=self.request.user)
		if department := self.request.GET.get('department'):
			qs = qs.filter(Q(student__department=department))
		if specialization := self.request.GET.get('specialization'):
			qs = qs.filter(Q(student__specialization=specialization))
		if zone := self.request.GET.get('zone'):
			qs = qs.filter(Q(zone=zone))
		if assessment_type := self.request.GET.get('assessment_type'):
			qs = qs.filter(Q(student_sections__section__assessment_type=assessment_type)).distinct()
		if assessor := self.request.GET.get('assessor'):
			qs = qs.filter(Q(assessor__pk=assessor))
		if from_date := self.request.GET.get('from_date'):
			if  from_time := self.request.GET.get('from_time'):
				from_time = datetime.time(from_time)
			else:
				from_time = datetime.time(00,00)
			timezone_aware_from_time = timezone.make_aware(datetime.datetime.combine(datetime.datetime.strptime(from_date, '%Y-%m-%d'), from_time))
			qs = qs.filter(created_at__gt=timezone_aware_from_time)
		if to_date := self.request.GET.get('to_date'):
			if  to_time := self.request.GET.get('to_time'):
				to_time = datetime.time(to_time)
			else:
				to_time = datetime.time(00,00)
			timezone_aware_to_time = timezone.make_aware(datetime.datetime.combine(datetime.datetime.strptime(to_date, '%Y-%m-%d'), to_time))
			qs = qs.filter(created_at__lt=timezone_aware_to_time)	
		search_query = self.request.GET.get('search_query')
		if search_query:
			qs = qs.filter(Q(student__full_name__icontains=search_query) | Q(student__index__icontains=search_query) | Q(school__icontains=search_query) | Q(grade__icontains=search_query) | Q(learning_area__icontains=search_query) | Q(zone__icontains=search_query) | Q(assessor__full_name__icontains=search_query))
		return qs.order_by('student')

class DeleteStudentLetterView(LoginRequiredMixin, AdminMixin, View):
	def post(self, request, letter_id, *args, **kwargs):
		letter = StudentLetter.objects.get(pk=letter_id)
		letter.delete()
		log_custom_action(request.user, letter, DELETION)
		messages.success(request, f'Deleted the Student letter {letter.student.full_name}')
		return redirect(reverse_lazy('invalid_assessments'))

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
		return context
	
	def form_valid(self, form):
		form = self.get_form(self.get_form_class())
		student_section = self.kwargs.get('pk')
		student_letter = StudentSection.objects.get(pk=student_section).student_letter
		student_sections = StudentSection.objects.filter(student_letter=student_letter)		
		score =0
		for section in student_sections:
			score += section.score
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

class StudentSectionsViewList(LoginRequiredMixin, ActivePeriodMixin, ListView):
	model = StudentSection
	template_name = 'teaching_practice/student_sections.html'
	context_object_name = 'studentsections'
	paginate_by = 50

	def get_queryset(self):
		qs = StudentSection.objects.all()
		search_query = self.request.GET.get('search_query')
		if search_query:
			qs = qs.filter(Q(student__full_name__icontains=search_query) | Q(student__index__icontains=search_query) | Q(section__name__icontains=search_query))
		return qs.order_by('student')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['search_query'] = SearchForm(self.request.GET)
		return context

class NewStudentAspectView(LoginRequiredMixin, ActivePeriodMixin, CreateView):
	model = StudentAspect
	form_class = NewStudentAspect
	template_name = 'teaching_practice/base_form.html'
	success_url = reverse_lazy('studentaspects')

	def get_context_data(self, **kwargs):
		user = self.request.user
		student_section_id = self.kwargs.get('pk')
		student_section = StudentSection.objects.get(pk=student_section_id)
		section = Section.objects.get(pk=student_section.section)
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
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
			if student_letter.assessor == self.request.user:
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
		qs  = StudentAspect.objects.all()
		search_query = self.request.GET.get('search_query')
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
		assessment_type = StudentSection.objects.filter(student_letter=student_letter).first().section.assessment_type
		if assessment_type == 'PHE':
			return ['teaching_practice/phe_pdf_report.html']
		elif assessment_type == 'General':
			return ['teaching_practice/general_pdf_report.html']
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
	
class ZonesViewList(LoginRequiredMixin, ListView):
	model = StudentLetter
	template_name = 'teaching_practice/zonal_leader.html'
	context_object_name = 'studentletters'
	paginate_by = 50

	def get_queryset(self):
		user = self.request.user
		zonal_leaders = ZonalLeader.objects.all().values_list('assessor__pk', flat=True)
		if user.is_staff:
			qs = StudentLetter.objects.all()
		elif user.pk in zonal_leaders:
			zone = ZonalLeader.objects.get(assessor=user)
			qs = StudentLetter.objects.filter(zone=zone)
		else:
			raise PermissionDenied
		if department := self.request.GET.get('department'):
			qs = qs.filter(Q(student__department=department))
		if specialization := self.request.GET.get('specialization'):
			qs = qs.filter(Q(student__specialization=specialization))
		if zone := self.request.GET.get('zone'):
			qs = qs.filter(Q(zone=zone))
		if assessment_type := self.request.GET.get('assessment_type'):
			qs = qs.filter(Q(student_sections__section__assessment_type=assessment_type)).distinct()
		if assessor := self.request.GET.get('assessor'):
			qs = qs.filter(Q(assessor__pk=assessor))
		if from_date := self.request.GET.get('from_date'):
			if  from_time := self.request.GET.get('from_time'):
				from_time = datetime.time(from_time)
			else:
				from_time = datetime.time(00,00)
			timezone_aware_from_time = timezone.make_aware(datetime.datetime.combine(datetime.datetime.strptime(from_date, '%Y-%m-%d'), from_time))
			qs = qs.filter(created_at__gt=timezone_aware_from_time)
		if to_date := self.request.GET.get('to_date'):
			if  to_time := self.request.GET.get('to_time'):
				to_time = datetime.time(to_time)
			else:
				to_time = datetime.time(00,00)
			timezone_aware_to_time = timezone.make_aware(datetime.datetime.combine(datetime.datetime.strptime(to_date, '%Y-%m-%d'), to_time))
			qs = qs.filter(created_at__lt=timezone_aware_to_time)
		search_query = self.request.GET.get('search_query')
		if search_query:
			qs = qs.filter(Q(student__full_name__icontains=search_query) | Q(student__index__icontains=search_query) | Q(school__icontains=search_query) | Q(grade__icontains=search_query) | Q(learning_area__icontains=search_query) | Q(zone__icontains=search_query) | Q(assessor__icontains=search_query))
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
		user = self.request.user
		zonal_leaders = ZonalLeader.objects.all().values_list('assessor', flat=True)
		context = super().get_context_data(**kwargs)
		if user.is_staff:
			context['zonal_leaders'] = ZonalLeader.objects.all()
		elif user in zonal_leaders:
			zone = ZonalLeader.objects.get(assessor=user)
			context['zonal_leaders'] = ZonalLeader.objects.filter(zone=zone)
		else:
			context['zonal_leaders'] = ZonalLeader.objects.none()
		context['is_nav_enabled'] = True
		context['title'] = 'Zonal Leaders'
		return context
	
class RequestDeletionView(LoginRequiredMixin, View):
	def post(self, *args, **kwargs):
		obj_id = self.kwargs.get('pk')
		path = self.kwargs.get('path')
		print(path)
		request_deletion(self.request, obj_id, path)
		messages.success(self.request, 'Your request for deletion has been sent successfully. The admin will review it and take action if necessary.')
		return redirect(path)
	
class DeleteObject(LoginRequiredMixin, DeleteView):
	model = Aspect
	success_url = reverse_lazy('aspects')
	template_name = 'teaching_practice/aspect_confirm_delete.html'

	def get_object(self, queryset = None):
		
		return super().get_object(queryset)

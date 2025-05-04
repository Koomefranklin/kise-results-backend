from email import errors, message
from turtle import st
from django.conf.locale import fi
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render, redirect
from dal import autocomplete
from django.template import context
from django.views.generic.base import View
from django.urls import reverse_lazy
from dev.forms import CustomUserCreationForm
from dev.models import User
from teaching_practice.mailer import send_student_report
from .forms import NewAspect, NewLocationForm, NewSection, NewStudentAspect, NewStudentForm, NewStudentLetter, NewStudentSection, NewSubSection, SearchForm, StudentForm, UpdateAspect, UpdateSection, UpdateStudentAspect, UpdateStudentLetter, UpdateStudentSection, StudentAspectFormSet, UpdateSubSection
from .models import Student, Section, StudentAspect, StudentLetter, StudentSection, Aspect, Location, SubSection, ZonalLeader
from django.views.generic import ListView, CreateView, FormView, UpdateView, DeleteView, DetailView
from django.db.models import Q, Avg, F, ExpressionWrapper, FloatField, Value
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.gis.geos import Point
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django_weasyprint import WeasyTemplateResponseMixin
import tempfile
from django.db.models.fields import Field


# Create your views here.

class StudentAutocomplete(autocomplete.Select2QuerySetView):
	def get_queryset(self):
		user = self.request.user
		qs = User.objects.filter(Q(is_active=True) | Q(role='student'))
		if self.q:
			qs = qs.filter(Q(full_name__icontains=self.q))
		return qs

class IndexPage(LoginRequiredMixin, ListView):
	model = User
	template_name = 'teaching_practice/index.html'
	context_object_name = 'dashboard'

	def get_queryset(self):
		return User.objects.filter(pk=self.request.user.pk)
	
	def get_context_data(self, **kwargs):
		user = self.request.user
		students = Student.objects.all()
		letters = StudentLetter.objects.all()
		sections = Section.objects.all()
		aspects = Aspect.objects.all()

		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Teaching Practice Home'
		context['letters'] = letters.count()
		context['students'] = students.count()
		context['sections'] = sections.count()
		context['aspects'] = aspects.count()
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
	
	def post(self, request, *args, **kwargs):
		form = self.get_form(self.get_form_class())
		if form.is_valid:
			instance = form.save(commit=False)
			instance.created_by = self.request.user
			instance.save()
		return super().post(request, *args, **kwargs)

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
	paginate_by = 50

	def get_queryset(self):
		qs = Section.objects.all()
		search_query = self.request.GET.get('search_query')
		if search_query:
			qs = qs.filter(Q(name__icontains=search_query) | Q(score__icontains=search_query))
		return qs.order_by('number')
	
	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Sections'
		context['search_query'] = SearchForm(self.request.GET)
		return context
	
class NewSubSectionView(LoginRequiredMixin, CreateView):
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

class EditSubSectionView(LoginRequiredMixin, UpdateView):
	model = SubSection
	form_class = UpdateSubSection
	template_name = 'teaching_practice/base_form.html'
	success_url = reverse_lazy('sub_sections')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
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

class NewAspectView(LoginRequiredMixin, CreateView):
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
			return instance

class EditAspectView(LoginRequiredMixin, UpdateView):
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
	
class NewStudentView(LoginRequiredMixin, CreateView):
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
	
class EditStudentView(LoginRequiredMixin, UpdateView):
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
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Students'
		context['search_query'] = SearchForm(self.request.GET)
		context['location_form'] = NewLocationForm(self.request.POST)
		return context
	
	def get_queryset(self):
		qs = Student.objects.all()
		search_query = self.request.GET.get('search_query')
		if search_query:
			qs = qs.filter(full_name__icontains=search_query)
		return qs.order_by('full_name')

class NewStudentLetterView(LoginRequiredMixin, View):
	def post(self, request, *args, **kwargs):
		longitude = self.kwargs.get('longitude')
		latitude = self.kwargs.get('latitude')
		student_id = self.kwargs.get('student_id')

		if latitude and longitude:
			try:
				point = Point(float(longitude), float(latitude))
				location_instance = Location.objects.create(point=point)
			except ValueError:
				location_instance = None
		else:
			location_instance = None

		student_instance = Student.objects.get(pk=student_id)

		student_letter, created = StudentLetter.objects.get_or_create(student=student_instance, 
			assessor=self.request.user, defaults={'location':location_instance})
		if created:
			location_instance.save()
			messages.success(self.request, f'Location Created Successfully')
			sections = Section.objects.all()

			for section in sections:
				student_section = StudentSection.objects.create(student_letter=student_letter, section=section)
				aspects = Aspect.objects.filter(section=section)
				for aspect in aspects:
					student_aspect = StudentAspect.objects.create(student_section=student_section, aspect=aspect)

			messages.success(self.request, f'Added {student_letter.student} Successfully')

		return redirect(reverse_lazy('edit_student_details', kwargs={'student_letter': student_letter.pk}))
	
class PreviousAssessmentsView(LoginRequiredMixin, ListView):
	model = StudentLetter
	template_name = 'teaching_practice/previous_assessments.html'
	paginate_by = 5

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
		return context

class EditStudentLetterView(LoginRequiredMixin, UpdateView):
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
			form.instance.assessor = self.request.user
			response = super().form_valid(form)
			student_letter = self.get_object()
			sections = StudentSection.objects.filter(student_letter=student_letter)
			uncommented_sections = []
			student = student_letter.student
			null_fields = []
			for field in student._meta.get_fields():
				if isinstance(field, Field):
					value = getattr(student, field.name)
					if value is None:
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
		return context
	
class EditStudentDetailsView(LoginRequiredMixin, View):
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
			letter = letter_form.save(commit=True)

			student = student_form.save(commit=True)
			messages.success(self.request, f'Updated {student.full_name} Successfully')
			return redirect(reverse_lazy('edit_student_letter', kwargs={'pk': letter.pk}))

	
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
		return context
	
	def get_queryset(self):
		if self.request.user.is_staff:
			qs = StudentLetter.objects.all()
		else:
			qs = StudentLetter.objects.filter(assessor=self.request.user)
		search_query = self.request.GET.get('search_query')
		if search_query:
			qs = qs.filter(Q(student__full_name__icontains=search_query) | Q(student__index__icontains=search_query) | Q(school__icontains=search_query) | Q(grade__icontains=search_query) | Q(learning_area__icontains=search_query) | Q(zone__icontains=search_query) | Q(assessor__full_name__icontains=search_query))
		return qs.order_by('student')

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

class EditStudentSectionView(LoginRequiredMixin, UpdateView):
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
		student_letter.assessor = self.request.user
		student_letter.save()

		response = super().form_valid(form)
		if "save_continue" in self.request.POST:
			student_section = StudentSection.objects.get(pk=student_section)
			current_number = student_section.section.number
			student_letter = student_section.student_letter
			last_number = Section.objects.all().count()
			if current_number != last_number:
				next_number = current_number + 1
				next_section = StudentSection.objects.get(Q(section__number=next_number) & Q(student_letter=student_letter)).pk
				return redirect(reverse_lazy('edit_student_aspects', kwargs={'pk': next_section}))
		return response

class StudentSectionsViewList(LoginRequiredMixin, ListView):
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

class NewStudentAspectView(LoginRequiredMixin, CreateView):
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
		# context['title'] = 
		return context

class EditStudentAspectView(LoginRequiredMixin, View):
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
		}

		if formset.is_valid():
			errors = []
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
	template_name = 'teaching_practice/generate_pdf.html'

	def get_object(self):
		return get_object_or_404(StudentLetter, pk=self.kwargs.get('pk'))
	
	def get_pdf_filename(self):
		student = StudentLetter.objects.get(pk=self.kwargs.get('pk')).student
		return f'{student.full_name}.pdf'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		letter = self.get_object()
		sections = StudentSection.objects.prefetch_related('student_aspects').filter(student_letter=letter)
		aspects = StudentAspect.objects.filter(student_section__student_letter=letter)

		context['is_nav_enabled'] = True
		context["title"] = f'{letter.student.full_name}\'s Assessment Report'
		context['letter'] = letter
		context['sections'] = sections
		context['aspects'] = aspects
		return context
	
	def render_to_response(self, context, **response_kwargs):
		response = super().render_to_response(context, **response_kwargs)

		response.render()

		with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmpfile:
			tmpfile.write(response.content)
			tmpfile.seek(0)

		send_student_report(self.request, tmpfile.name, self.get_object())

		return response
	
class ZonesViewList(LoginRequiredMixin, ListView):
	model = StudentLetter
	template_name = 'teaching_practice/zonal_leader.html'
	context_object_name = 'studentletters'
	paginate_by = 50

	def get_queryset(self):
		user = self.request.user
		zonal_leaders = ZonalLeader.objects.all().values_list('assessor', flat=True)
		if user.is_staff:
			qs = StudentLetter.objects.all()
		elif user in zonal_leaders:
			zone = ZonalLeader.objects.get(assessor=user)
			qs = StudentLetter.objects.filter(zone=zone)
		else:
			raise PermissionDenied
		search_query = self.request.GET.get('search_query')
		if search_query:
			qs = qs.filter(Q(student__full_name__icontains=search_query) | Q(student__index__icontains=search_query) | Q(school__icontains=search_query) | Q(grade__icontains=search_query) | Q(learning_area__icontains=search_query) | Q(zone__icontains=search_query) | Q(assessor__icontains=search_query))
		return qs.order_by('student')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Zonal Leader'
		context['search_query'] = SearchForm(self.request.GET)
		return context
	
class DeleteObject(LoginRequiredMixin, DeleteView):
	model = Aspect
	success_url = reverse_lazy('aspects')
	template_name = 'teaching_practice/aspect_confirm_delete.html'

	def get_object(self, queryset = None):
		
		return super().get_object(queryset)
		
from django.shortcuts import get_object_or_404, render, redirect
from dal import autocomplete
from django.views.generic.base import View
from django.urls import reverse_lazy
from dev.forms import CustomUserCreationForm
from dev.models import User
from .forms import NewAspect, NewLocationForm, NewSection, NewStudentAspect, NewStudentForm, NewStudentLetter, NewStudentSection, NewSubSection, SearchForm, StudentForm, UpdateAspect, UpdateSection, UpdateStudentAspect, UpdateStudentLetter, UpdateStudentSection, StudentAspectFormSet, UpdateSubSection
from .models import Student, Section, StudentAspect, StudentLetter, StudentSection, Aspect, Location, SubSection
from django.views.generic import ListView, CreateView, FormView, UpdateView, DeleteView, DetailView
from django.db.models import Q, Avg, F, ExpressionWrapper, FloatField, Value
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.gis.geos import Point
from django.http import HttpResponse, HttpResponseRedirect
from django_weasyprint import WeasyTemplateResponseMixin


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

		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Home'
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
			print(instance.created_by)
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
	paginate_by = 20

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
	paginate_by = 20

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
	model = User
	form_class = CustomUserCreationForm
	template_name = 'teaching_practice/base_form.html'
	success_url = reverse_lazy('students_tp')

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'New Student'
		return context

class StudentsViewList(LoginRequiredMixin, ListView):
	model = User
	template_name = 'teaching_practice/students.html'
	context_object_name = 'students'
	paginate_by = 20

	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Students'
		context['search_query'] = SearchForm(self.request.GET)
		return context
	
	def get_queryset(self):
		qs = User.objects.all()
		search_query = self.request.GET.get('search_query')
		if search_query:
			qs = qs.filter(full_name__icontains=search_query)
		return qs.order_by('full_name')

class NewStudentLetterView(LoginRequiredMixin, FormView):
	model = StudentLetter
	form_class = NewStudentForm
	template_name = 'teaching_practice/new_student_letter.html'
	success_url = reverse_lazy('student_letters')
	
	def get_context_data(self, **kwargs):
		user = self.request.user
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		if 'student_letter_form' not in context:
			context['student_letter_form'] = NewStudentLetter()
		if 'location_form' not in context:
			context['location_form'] = NewLocationForm()
		context['title'] = 'New Student Letter'
		return context
	
	def post(self, request, *args, **kwargs):
		student_form = self.get_form(self.get_form_class())
		student_letter_form = NewStudentLetter(self.request.POST)
		location_form = NewLocationForm(self.request.POST)

		if student_letter_form.is_valid() and student_form.is_valid() and location_form.is_valid():
			location_data = location_form.cleaned_data
			longitude = location_data['longitude']
			latitude = location_data['latitude']

			if latitude and longitude:
				try:
					point = Point(float(longitude), float(latitude))
					location_instance = Location.objects.create(point=point)
				except ValueError:
					location_instance = None
			else:
				location_instance = None

			location_instance.save()
			messages.success(self.request, f'Location Created Successfully')
			student_instance = student_form.save()

			student_letter = student_letter_form.save(commit=False)
			student_letter.location = location_instance			
			student_letter.student = student_instance
			student_letter.assessor = self.request.user
			student_letter.save()

			sections = Section.objects.all()

			for section in sections:
				student_section = StudentSection.objects.create(student_letter=student_letter, section=section)
				aspects = Aspect.objects.filter(section=section)
				for aspect in aspects:
					student_aspect = StudentAspect.objects.create(student_section=student_section, aspect=aspect)

			messages.success(self.request, f'Added {student_letter.student} Successfully')

			return redirect(self.get_success_url())

		return self.form_invalid(student_letter_form, student_form, location_form)
	
	def form_invalid(self, student_letter_form, student_form, location_form):
		"""
		Renders the forms again with errors when validation fails.
		"""
		context = self.get_context_data()
		context['student_letter_form'] = student_letter_form
		context['form'] = student_form
		context['location_form'] = location_form
		return self.render_to_response(context)

class EditStudentLetterView(LoginRequiredMixin, UpdateView):
	model = StudentLetter
	form_class = UpdateStudentLetter
	template_name = 'teaching_practice/update_student_letter.html'
	
	def get_success_url(self):
		student_letter_id = self.kwargs.get('pk')
		return reverse_lazy('pdf_report', kwargs={'pk': student_letter_id})

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
		context['sections'] =student_sections
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
		context['title'] = 'Student Letters'
		context['search_query'] = SearchForm(self.request.GET)
		return context
	
	def get_queryset(self):
		qs = StudentLetter.objects.all()
		search_query = self.request.GET.get('search_query')
		if search_query:
			qs = qs.filter(Q(student__user__full_name__icontains=search_query) | Q(student__index__icontains=search_query))
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
		section = StudentSection.objects.get(pk=student_section).section
		student_aspects = StudentAspect.objects.filter(student_section=student_section)
		context = super().get_context_data(**kwargs)
		context['is_nav_enabled'] = True
		context['title'] = 'Section Scores'
		context['aspects'] = student_aspects
		context['section'] = section
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
		return super().form_valid(form)

class StudentSectionsViewList(LoginRequiredMixin, ListView):
	model = StudentSection
	template_name = 'teaching_practice/student_sections.html'
	context_object_name = 'studentsections'
	paginate_by = 20

	def get_queryset(self):
		qs = StudentSection.objects.all()
		search_query = self.request.GET.get('search_query')
		if search_query:
			qs = qs.filter(Q(student__user__full_name__icontains=search_query) | Q(student__index__icontains=search_query) | Q(section__name__icontains=search_query))
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

		queryset = StudentAspect.objects.filter(student_section=student_section)
		formset = StudentAspectFormSet(queryset=queryset)

		context = {
			'is_nav_enabled': True,
			'title': 'Add Aspect Scores',
			'section': student_section,
			'formset': formset,
		}

		return render(request, self.template_name, context)

	def post(self, request, *args, **kwargs):
		student_section_id = self.kwargs.get('pk')
		student_section = get_object_or_404(StudentSection, pk=student_section_id)

		queryset = StudentAspect.objects.filter(student_section=student_section)
		formset = StudentAspectFormSet(request.POST, queryset=queryset)

		if formset.is_valid():
			formset.save()
			student_aspects = StudentAspect.objects.filter(student_section=student_section)
			sum = 0
			for aspect in student_aspects:
				sum += aspect.score
			student_section.score = sum
			student_section.save()
			return redirect(self.get_success_url())

		context = {
			'is_nav_enabled': True,
			'title': 'Add Aspect Scores',
			'section': student_section,
			'formset': formset,
		}
		return render(request, self.template_name, context)

class StudentAspectsViewList(LoginRequiredMixin, ListView):
	model = StudentAspect
	template_name = 'teaching_practice/student_aspects.html'
	context_object_name = 'studentaspects'
	paginate_by = 20

	def get_queryset(self):
		qs  = StudentAspect.objects.all()
		search_query = self.request.GET.get('search_query')
		if search_query:
			qs = qs.filter(Q(student__user__full_name__icontains=search_query) | Q(student__index__icontains=search_query) | Q(aspect__name__icontains=search_query) | Q(aspect__section__name__icontains=search_query))
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
		return f'{student.user.full_name}.pdf'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		letter = self.get_object()
		sections = StudentSection.objects.prefetch_related('student_aspects').filter(student_letter=letter)
		aspects = StudentAspect.objects.filter(student_section__student_letter=letter)

		context['is_nav_enabled'] = True
		context["title"] = 'Generate Report'
		context['letter'] = letter
		context['sections'] = sections
		context['aspects'] = aspects
		return context

	
class DeleteObject(LoginRequiredMixin, DeleteView):
	model = Aspect
	success_url = reverse_lazy('aspects')
	template_name = 'teaching_practice/aspect_confirm_delete.html'

	def get_object(self, queryset = None):
		
		return super().get_object(queryset)
		
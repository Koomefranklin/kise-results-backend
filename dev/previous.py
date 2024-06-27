# from dal import autocomplete
# from .forms import ScoreForm, StudentPaperUpdateForm, KnecIndexForm
# class StudentAutocomplete(autocomplete.Select2QuerySetView):
#   def get_queryset(self):
#     user = self.request.user
#     course = Lecturer.objects.get(user=user).department
#     qs = Specialization.objects.filter(course= course)
#     if self.q:
#       qs = qs.filter(Q(student__user__surname__icontains=self.q) | Q(student__user__other_names__icontains=self.q) | Q(student__admission__icontains=self.q))
#     students = qs.values_list('student', flat=True)
#     return Student.objects.filter(pk__in=students)
  
# class ModuleAutocomplete(autocomplete.Select2QuerySetView):
#   def get_queryset(self):
#     user = self.request.user
#     course = Lecturer.objects.get(user=user).department
#     # paper = Paper.objects.get(pk=self.kwargs.get('paper'))
#     qs = Module.objects.filter(paper__course=course)
#     if self.q:
#       qs = qs.filter(Q(code__icontains=self.q) | Q(name__icontains=self.q))
#     return qs



# class IndexPage(LoginRequiredMixin, ListView):
#   template_name = 'results/index.html'
#   context_object_name = 'context'
#   model = Paper
#   queryset = Paper.objects.all()

#   # def get_queryset(self):
#   #   user = self.request.user
#   #   queryset = Paper.objects.all()
#   #   return queryset

#   def get_context_data(self, **kwargs):
#     user = self.request.user
#     course = Lecturer.objects.get(user=user).department
#     context = super().get_context_data(**kwargs)
#     context['has_permission'] = user
#     context['is_student'] = True if user.role == 'student' else False
#     context['is_lecturer'] = not context['is_student']
#     context['y1'] = self.queryset.filter(course__session__period=1).all()
#     context['dly2'] = self.queryset.filter(Q(course__session__period=2) & Q(course__session__mode='DL') & Q(course=course)).all()
#     context['fty2'] = self.queryset.filter(Q(course__session__period=2) & Q(course__session__mode='FT') & Q(course=course)).all()
#     context['is_tl'] = TeamLeader.objects.get(lecturer__user=user)
#     return context

# # class PaperResult(LoginRequiredMixin, ListView):
# #   model = Result
# #   template_name = 'results/paper_result.html'
# #   context_object_name = 'students'
# #   paginate_by = 50


# #   def get_queryset(self):
# #     user = self.request.user    
# #     queryset = Result.objects.filter(paper__pk=self.kwargs['paper']).all().order_by('cat1')
# #     search_query = self.request.GET.get('query')
# #     query =  Q(student__user__surname__icontains=search_query) | Q(student__user__other_names__icontains=search_query) | Q(student__admission__icontains=search_query)
# #     if search_query:
# #       queryset = queryset.filter(query).order_by('cat1')
# #     return queryset
  
# #   def get_context_data(self, **kwargs):
# #     lecturer = Lecturer.objects.get(user=self.request.user)
# #     context = super().get_context_data(**kwargs)
# #     context['has_permission'] = self.request.user
# #     context['resultform'] = ResultForm(self)
# #     context['indexform'] = KnecIndexForm(self)
# #     context['total'] = Result.objects.all().count()
# #     context['is_nav_sidebar_enabled'] = True
# #     context['is_lecturer'] = lecturer
# #     context['paper'] = Paper.objects.get(pk=self.kwargs['paper'])
# #     # context['lecturer_units'] = LecturerUnit.objects.filter(lecturer__user=self.request.user).values_list('unit', flat=True)
# #     return context
  
# #   def get_forms(self):
# #     resultform = ResultForm(prefix='resultform')
# #     indexform = KnecIndexForm(prefix='indexform')
# #     return {'resultform': resultform, 'indexform': indexform}
  
# #   def post(self, request, *args, **kwargs):
# #     resultform = ResultForm(self, request.POST)
# #     indexform = KnecIndexForm(request.POST)
# #     resultform.initial['paper'] = Paper.objects.get(pk=self.kwargs.get('paper'))
# #     if resultform.is_valid() and indexform.is_valid() :
# #       resultform.save()

# #       student = resultform.cleaned_data['student']

# #       indexform.instance.student = student

# #       indexform.save()
# #     else:
# #       print('result')
# #       print(resultform.errors)
# #       print('index')
# #       print(indexform.errors)
# #     return self.get(request, *args, **kwargs)
  
# class StudentResult(LoginRequiredMixin, ListView):
#   model = Result
#   template_name = 'results/student_result.html'
#   context_object_name = 'results'
#   queryset = Result.objects.all()

#   def get_context_data(self, **kwargs):
#     user = self.request.user
#     context = super().get_context_data(**kwargs)
#     context['is_student'] = True if user.role == 'student' else False
#     context['has_permission'] = user
#     if user.role == 'student':
#       context['y1'] = self.queryset.filter(Q(student__user=user) & Q(paper__course__session__period=1)).all()
#       context['y2'] = self.queryset.filter(Q(student__user=user) & Q(paper__course__session__period=2)).all()
#       context['course1'] = Course.objects.get(session__mode='CM')
#       context['course2'] = Specialization.objects.get(student__user=user)
#     else:
#       context['is_nav_sidebar_enabled'] = True
#     return context
  
# class CourseResults(LoginRequiredMixin, ListView):
#   model = Result
#   template_name = 'results/course_results.html'
#   context_object_name = 'results'

#   def get_queryset(self):
#     user = self.request.user
#     course = TeamLeader.objects.get(lecturer__user=user).course
#     papers = Paper.objects.filter(course=course)
#     results = Result.objects.filter(paper__in=papers)
#     return results
  
#   def get_context_data(self, **kwargs):
#     user = self.request.user
#     context = super().get_context_data(**kwargs)
#     context['has_permission'] = user
#     context['is_student'] = True if user.role == 'student' else False
#     context['is_lecturer'] = not context['is_student']
#     context['is_tl'] = TeamLeader.objects.get(lecturer__user=user)
#     context['is_nav_sidebar_enabled'] = True
#     return context

# class StudentPaperUpdate(LoginRequiredMixin, UpdateView):
#   model = Result
#   template_name = 'results/result_update.html'
#   form_class = StudentPaperUpdateForm

#   def get_success_url(self):
#     paper = Result.objects.get(pk=self.kwargs['pk']).paper.pk
#     return reverse_lazy('single_paper', kwargs={'paper':paper})

#   def get_context_data(self, **kwargs):
#     user = self.request.user
#     context = super().get_context_data(**kwargs)
#     context['has_permission'] = user
#     context['is_student'] = True if user.role == 'student' else False
#     context['is_lecturer'] = not context['is_student']
#     context['is_tl'] = TeamLeader.objects.get(lecturer__user=user)
#     context['is_nav_sidebar_enabled'] = True
#     context['details'] = Result.objects.get(pk=self.kwargs['pk'])
#     return context
  
# class ScoreView(LoginRequiredMixin, ListView):
#   model = ModuleScore
#   template_name = 'results/new_score.html'
#   queryset = ModuleScore.objects.all()
  
#   def get_context_data(self, **kwargs):
#     lecturer = Lecturer.objects.get(user=self.request.user)
#     context = super().get_context_data(**kwargs)
#     context['has_permission'] = self.request.user
#     context['form'] = ScoreForm(self)
#     context['total'] = Result.objects.all().count()
#     context['is_nav_sidebar_enabled'] = True
#     context['is_lecturer'] = lecturer
#     context['paper'] = Paper.objects.get(pk=self.kwargs['paper'])
#     return context
    
#   def post(self, request, *args, **kwargs):
#     form = ScoreForm(request.POST)
#     if form.is_valid():
#       form.save()
#     else:
#       print(form.errors)
#     return self.get(request, *args, **kwargs)
  
# class ResultsListView(LoginRequiredMixin, ListView):
#   model = Result
#   template_name = 'results/all.html'
#   context_object_name = 'instances'
#   queryset = ModuleScore.objects.all()

#   def get_queryset(self):     
#     return super().get_queryset()
  
#   def get_context_data(self, **kwargs):
#     context = super().get_context_data(**kwargs)
#     user = self.request.user
#     paper=self.kwargs['paper']
#     course = Paper.objects.get(pk=paper).course
#     context['paper'] = Paper.objects.get(pk=paper)
#     context['has_permission'] = user
#     context['is_student'] = True if user.role == 'student' else False
#     context['is_lecturer'] = not context['is_student']
#     context['is_tl'] = TeamLeader.objects.get(lecturer__user=user)
#     context['is_nav_sidebar_enabled'] = True
#     scores = ModuleScore.objects.all()
#     students = Specialization.objects.filter(course=course).values_list('student', flat=True).distinct()
#     combinations = CatCombination.objects.get(paper=paper)
#     cat1modules = combinations.cat1.all()
#     cat2modules = combinations.cat2.all()
#     context['mo'] = students
#     cat1 = 0
#     cat2 = 0
#     results = []
    
#     for student in students:
#       student_object = Student.objects.get(admission=student)
#       result = {}
#       for score in scores:
#         if score.student.admission == student:
#           if score.module in cat1modules:
#             cat1 += score.score
#           elif score.module in cat2modules:
#             cat2 += score.score
#         result['student'] = student_object
#         result['cat1'] = cat1
#         result['cat2'] = cat2
#       results.append(result)
#     context['results'] = chain(results)
#     context['s'] = student_object
#     return context

# path('', views.IndexPage.as_view(), name='index'),
  # path('paperResult/<str:paper>', views.ScoreView.as_view(), name='single_paper'),
  # path('student', views.StudentResult.as_view(), name='student_result'),
  # path('course/<int:pk>', views.CourseResults.as_view(), name='course_results'),
  # re_path(r'^student-autocomplete/$', views.StudentAutocomplete.as_view(), name='student_autocomplete'),
  # re_path(r'^module-autocomplete/$', views.ModuleAutocomplete.as_view(), name='module_autocomplete'),
  # path('update/<str:pk>', views.StudentPaperUpdate.as_view(), name='result_update'),
  # path('all/<str:paper>', views.ResultsListView.as_view(), name='all'),
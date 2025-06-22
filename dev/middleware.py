from django.shortcuts import redirect
from django.urls import reverse_lazy
import logging
from django.shortcuts import render

class FirstLoginMiddleware:
  def __init__(self, get_response):
    self.get_response = get_response

  def __call__(self, request):
    if request.user.is_authenticated:
      if request.user.is_first_login:
        if not request.path.startswith('/change-password/'):
          return redirect(reverse_lazy('first_password_change', kwargs={'pk': request.user.pk}))

    return self.get_response(request)

class ExceptionMiddleware:
	def __init__(self, get_response):
		self.get_response = get_response
		self.logger = logging.getLogger(__name__)

	def __call__(self, request):
		try:
			return self.get_response(request)
		except Exception as e:
               
			request.exception = e
			self.logger.error("Unhandled exception", exc_info=True)
			return render(request, 'errors/500.html', status=500, context={'title': 'Server error'})
from django.shortcuts import redirect
from django.urls import reverse_lazy

class FirstLoginMiddleware:
  def __init__(self, get_response):
    self.get_response = get_response

  def __call__(self, request):
    if request.user.is_authenticated:
      if request.user.is_first_login:
        if not request.path.startswith('/change-password/'):
          return redirect(reverse_lazy('first_password_change', kwargs={'pk': request.user.pk}))

    return self.get_response(request)
from django.core.mail import EmailMultiAlternatives
import os
from django.conf import settings
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages

admin_mail = ['fkoome@kise.ac.ke']

def send_student_report(request, file, obj):
  try:
    student = obj.student.full_name
    email = obj.student.email
    regards = 'Regards, KISE TP'
    sender_email = 'TP Assessment Reports <webform@kise.ac.ke>'
    subject, from_email, to = "KISE TEACHING PRACTICE ASSESSMENT REPORT", sender_email, email
    text_content = f'Attached is the assessment report for {student}'
    msg = EmailMultiAlternatives(subject=subject, body=text_content, from_email=from_email, to=[to])
    msg.mixed_subtype = 'related'
    msg.attach_file(file)
    msg.send()
    messages.success(request, f'Email sent to {student} at {email}')
  except Exception as e:
    with open('error.log', '+a') as error_file:
      error_file.write(f'{timezone.localtime(timezone.now())}: Error: {e}\n')
    messages.error(request, f'Error sending email to {student} at {email}.')

def send_otp(request, obj):
  try:
    user = obj.user
    email = user.email
    name = user.full_name
    otp = obj.otp
    sender_mail = 'TP Assessment <webform@kise.ac.ke>'
    html_content = f"""
    A password reset request was submiteed for {name}<br>
    Use the following OTP to verify and reset your password<br>
    This OTP will expire in 15 minutes.
    <strong>{otp}</strong> <br>
    <a href="{request.build_absolute_uri(reverse_lazy('reset_password', kwargs = {'username': user.username}))}">Proceed to resetL</a><br>
    """
    subject = 'Password Reset Request for TP Assessment module'
    msg = EmailMultiAlternatives(subject=subject, from_email=sender_mail, to=[email])
    msg.mixed_subtype = 'related'
    msg.attach_alternative(html_content, 'text/html')
    msg.send()
    messages.success(request, f'OTP sent to {email}')
  except Exception as e:
    with open('error.log', '+a') as error_file:
      error_file.write(f'{timezone.localtime(timezone.now())}: Error: {e}\n')
    messages.error(request, f'Error sending OTP to  {email}.')

def send_error(request, exception):
  try:
    sender_mail = 'TP Assessment <webform@kise.ac.ke>'
    
    method = request.method
    html_content = f"""
    
    <strong>An error {exception} occured in the site</strong><br>
     url: {request.build_absolute_uri()}<br>
     user: {request.user.full_name if request.user.is_authenticated else 'Anonymous'}<br>
     time: {timezone.localtime(timezone.now())}<br>
    The request was made using the {method} method.<br>
    data: {request.POST if method == 'POST' else request.GET}<br>
    """
    subject = 'Server Error'
    msg = EmailMultiAlternatives(subject=subject, from_email=sender_mail, to=admin_mail)
    msg.mixed_subtype = 'related'
    msg.attach_alternative(html_content, 'text/html')
    msg.send()
  except Exception as e:
    with open('error.log', '+a') as error_file:
      error_file.write(f'{timezone.localtime(timezone.now())}: Error: {e}\n')

def request_deletion(request, obj_id, path):
  try:
    user = request.user.full_name
    sender_mail = 'TP Assessment <webform@kise.ac.ke>'
    html_content = f"""
    A request for deletion of object {obj_id} from {path} was made by {user}<br>
    Please review the request and take appropriate action.<br>
    """
    subject = 'Deletion Request for TP Assessment module'
    msg = EmailMultiAlternatives(subject=subject, from_email=sender_mail, to=admin_mail)
    msg.mixed_subtype = 'related'
    msg.attach_alternative(html_content, 'text/html')
    msg.send()
    messages.success(request, f'Deletion request sent to {admin_mail}')
  except Exception as e:
    with open('error.log', '+a') as error_file:
      error_file.write(f'{timezone.localtime(timezone.now())}: Error: {e}\n')
    messages.error(request, f'Error sending deletion request to {admin_mail}.')

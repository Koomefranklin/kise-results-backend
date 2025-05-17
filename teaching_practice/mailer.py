from django.core.mail import EmailMultiAlternatives
import os
from django.conf import settings
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages

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
    <strong>{otp}</strong> 
    site url: {reverse_lazy('common')}<br>
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

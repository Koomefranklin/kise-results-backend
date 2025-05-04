from django.core.mail import EmailMultiAlternatives
import os
from django.conf import settings
from django.utils import timezone
from django.contrib import messages

def send_student_report(request, file, obj):
  try:
    student = obj.student.full_name
    email = obj.student.email
    regards = 'Regards, KISE TP'
    subject, from_email, to = "KISE TEACHING PRACTICE ASSESSMENT REPORT", None, email
    text_content = f'Attached is the assessment report for {student}'
    msg = EmailMultiAlternatives(subject=subject, body=text_content, from_email=from_email, to=[to])
    msg.mixed_subtype = 'related'
    msg.attach_file(file)
    msg.send()
    messages.success(request, f'Email sent to {student} at {email}')
  except Exception as e:
    with open('error.log', '+a') as error_file:
      error_file.write(f'{timezone.now()}: Error: {e}\n')
    messages.error(request, f'Error sending email to {student} at {email}.')
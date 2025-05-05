import csv
from django.core.management.base import BaseCommand
from dev.models import Lecturer, Specialization, User

class Command(BaseCommand):
	help = 'Import lecturers from a CSV file'

	def add_arguments(self, parser):
		parser.add_argument('csv_file', type=str, help='The path to the CSV file to be processed')

	def handle(self, *args, **kwargs):
		csv_file = kwargs['csv_file']

		try:
			with open(csv_file, mode='r') as file:
				reader = csv.DictReader(file)

				for row in reader:
					username = row['username']
					full_name = row['name']
					email = row['email']
					password = row['password']
					sex = row['sex']
					role = 'lecturer'					
					# department = row['department'].split(',')

					# specializations = Specialization.objects.filter(code__in=department).values_list('id', flat=True)
					user, created = User.objects.get_or_create(username=username, email=email, sex=sex, defaults={'full_name': full_name,  'role': role})
					# lecturer, created = Lecturer.objects.get_or_create(
					# 	user=user,
					# )
					# lecturer.specializations.add(*specializations)

					if created:
						user.set_password(password)
						user.save()
						self.stdout.write(self.style.SUCCESS(f"Successfully created Lecturer: {full_name}"))
					else:
						self.stdout.write(self.style.WARNING(f"Lecturer: {full_name}, already exists"))

		except FileNotFoundError:
			self.stdout.write(self.style.ERROR('CSV file not found.'))
		except Exception as e:
			self.stdout.write(self.style.ERROR(f"Error occurred: {str(e)}"))

import csv
from django.core.management.base import BaseCommand
from teaching_practice.models import Student

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
					name = row['name']
					# email = row['email']
					sex = row['sex']

					student, created = Student.objects.get_or_create(
						full_name=name,
            # email=email,
						sex=sex
					)

					if created:
						self.stdout.write(self.style.SUCCESS(f"Successfully created Student: {name}"))
					else:
						self.stdout.write(self.style.WARNING(f"Student: {name} already exists"))

		except FileNotFoundError:
			self.stdout.write(self.style.ERROR('CSV file not found.'))
		except Exception as e:
			self.stdout.write(self.style.ERROR(f"Error occurred: {str(e)}"))

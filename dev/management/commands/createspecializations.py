import csv
from django.core.management.base import BaseCommand
from dev.models import Course, Specialization, Mode

class Command(BaseCommand):
	help = 'Import specializations from a CSV file'

	def add_arguments(self, parser):
		parser.add_argument('csv_file', type=str, help='The path to the CSV file to be processed')

	def handle(self, *args, **kwargs):
		csv_file = kwargs['csv_file']

		try:
			with open(csv_file, mode='r') as file:
				reader = csv.DictReader(file)

				for row in reader:
					code = row['code']
					name = row['name']
					mode_code = row['mode']
					course_code = row['course']

					course = Course.objects.get(code=course_code)
					mode = Mode.objects.get(mode=mode_code)
					specialization, created = Specialization.objects.get_or_create(
						name=name,
						code=code,
						mode=mode,
						course=course
					)

					if created:
						self.stdout.write(self.style.SUCCESS(f"Successfully created Specialization: {name}"))
					else:
						self.stdout.write(self.style.WARNING(f"Specialization already exists: {name}"))

		except FileNotFoundError:
			self.stdout.write(self.style.ERROR('CSV file not found.'))
		except Exception as e:
			self.stdout.write(self.style.ERROR(f"Error occurred: {str(e)}"))

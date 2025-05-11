import csv
from django.core.management.base import BaseCommand
from dev.models import Specialization, Paper

class Command(BaseCommand):
	help = 'Import Papers from a CSV file'

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
					specialization_code = row['specialization']
					specialization = Specialization.objects.get(code=specialization_code)

					paper, created = Paper.objects.get_or_create(
						name=name,
						code=code,
						specialization=specialization
					)

					if created:
						self.stdout.write(self.style.SUCCESS(f"Successfully created Paper: {name}"))
					else:
						self.stdout.write(self.style.WARNING(f"Paper already exists: {name}"))

		except FileNotFoundError:
			self.stdout.write(self.style.ERROR('CSV file not found.'))
		except Exception as e:
			self.stdout.write(self.style.ERROR(f"Error occurred: {str(e)}"))

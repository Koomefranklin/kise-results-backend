import csv
from django.core.management.base import BaseCommand
from dev.models import Paper, Module

class Command(BaseCommand):
	help = 'Import modules from a CSV file'

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
					paper_code = row['paper']
					paper = Paper.objects.get(code=paper_code)

					module, created = Module.objects.get_or_create(
						name=name,
						code=code,
						paper=paper
					)

					if created:
						self.stdout.write(self.style.SUCCESS(f"Successfully created Module: {name}"))
					else:
						self.stdout.write(self.style.WARNING(f"Module already exists: {name}"))

		except FileNotFoundError:
			self.stdout.write(self.style.ERROR('CSV file not found.'))
		except Exception as e:
			self.stdout.write(self.style.ERROR(f"Error occurred: {str(e)}"))

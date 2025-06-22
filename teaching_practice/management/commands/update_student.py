import code
import csv
from operator import index
from django.core.management.base import BaseCommand
from dev.admin import Specialization
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
					name = (row['name']).upper()
					# paper_code = (row['paper']).upper()
					# admission = row['admission']
					# email = row['email']
					# index = row['index']
					sex = row['sex']
					# paper_code = admission.split('/')[0].replace('DSNE', '').upper()
					# specialization = Specialization.objects.get(short_name=paper_code)
					# self.stdout.write(self.style.SUCCESS(f"Processing student: {name} with specialization: {specialization}"))
					try:
						student = Student.objects.get(full_name=name)
						# student.specialization = specialization
						student.department = 'DL'
						student.save()
						self.stdout.write(self.style.SUCCESS(f"Student: {name} specialization added successfully"))
					except Student.DoesNotExist:
						self.stdout.write(self.style.ERROR(f"Student: {name} does not exists"))

		except FileNotFoundError:
			self.stdout.write(self.style.ERROR('CSV file not found.'))
		except Exception as e:
			self.stdout.write(self.style.ERROR(f"Error occurred: {str(e)}"))

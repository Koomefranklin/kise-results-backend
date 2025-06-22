import csv
from collections import defaultdict
from django.http import HttpResponse
from teaching_practice.models import StudentLetter 

def export_csv(request):
    data = defaultdict(list)

    # Group values by name
    for obj in StudentLetter.objects.exclude(comments=None):
        data[obj.student.full_name].append(obj.total_score)

    # Determine the max number of values per name to set column headers
    max_values = max(len(values) for values in data.values())

    # Column headers
    headers = ['Name'] + [f'Assessment_{i+1}' for i in range(max_values)]

    # Prepare the response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="export.csv"'

    writer = csv.writer(response)
    writer.writerow(headers)

    # Write each row
    for name, values in data.items():
        row = [name] + values + [''] * (max_values - len(values))  # pad if fewer items
        writer.writerow(row)

    return response

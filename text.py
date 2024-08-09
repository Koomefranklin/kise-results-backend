import json
new = ['Dr. Norman Kiogora',
'Kavulu Lilian',
'Malasi Flora M.N',
'Mbithi Ann N.',
'Mburu Peter Ndichu',
'Muchiru John Muga',
'Ong’era Lynett',
'Chege Elizabeth Nyambura',
'Nyakoa Ingolo Peris',
'Jennifer Mwenda Mwiti',
'Johnstone Lubanga',
'Sr. Gladys Rotich',
'Roseline Melly']
fixtures = []
i = 42
for value in new:
    fixture = {
        "model": "regalia.lecturers",
        "pk": i,
        "fields": {
            "full_name": value,
        }
    }

        # Append the fixture to the list
    fixtures.append(fixture)
    i += 1

# Save the fixtures to a JSON file
with open("regalia/fixtures/new.json", "w") as outfile:
    json.dump(fixtures, outfile, indent=2)
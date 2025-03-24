# import_blood_tests.py
import csv
from django.core.management.base import BaseCommand
from mhcapp.models import LabTest, Subtest

class Command(BaseCommand):
    help = 'Imports blood test data from CSV into the database'

    def handle(self, *args, **kwargs):
        csv_file_path = r'C:\Users\smabi\OneDrive - islingtoncollege.edu.np\Desktop\Health-app\mhcapp\management\commands\blood_tests.csv'  # Update this path
        
        with open(csv_file_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Get or create the Test
                test, created = LabTest.objects.get_or_create(name=row['test_name'])
                
                # Handle "N/A" values (replace with None)
                male_low = float(row['male_normal_range_low']) if row['male_normal_range_low'] != 'N/A' else None
                male_high = float(row['male_normal_range_high']) if row['male_normal_range_high'] != 'N/A' else None
                female_low = float(row['female_normal_range_low']) if row['female_normal_range_low'] != 'N/A' else None
                female_high = float(row['female_normal_range_high']) if row['female_normal_range_high'] != 'N/A' else None
                
                # Create Subtest
                Subtest.objects.create(
                    test=test,
                    name=row['subtest_name'],
                    male_normal_low=male_low,
                    male_normal_high=male_high,
                    female_normal_low=female_low,
                    female_normal_high=female_high,
                    unit=row['unit']
                )
        
        self.stdout.write(self.style.SUCCESS('Successfully imported data!'))
# mhcapp/management/commands/load_radiology_tests.py
import csv
from django.core.management.base import BaseCommand
from mhcapp.models import Modality, RadiologyTest

class Command(BaseCommand):
    help = 'Load radiology tests from a predefined CSV file'

    def handle(self, *args, **kwargs):
        # Replace this path with CSV file's location
        csv_file_path = r'C:\Users\smabi\OneDrive - islingtoncollege.edu.np\Desktop\Health-app\mhcapp\management\commands\radio_test.csv'  # 👈 Update this line
        
        try:
            with open(csv_file_path, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Get or create the modality
                    modality, _ = Modality.objects.get_or_create(
                        name=row['modality_name']
                    )
                    
                    # Create the radiology test
                    RadiologyTest.objects.get_or_create(
                        name=row['test_name'],
                        modality=modality
                    )
            
            self.stdout.write(self.style.SUCCESS(
                f'Successfully loaded {RadiologyTest.objects.count()} tests!'
            ))
        
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(
                f'CSV file not found at: {csv_file_path}. '
                'Please check the file path.'
            ))
# from django.test import TestCase, Client
# from django.urls import reverse
# from django.contrib.auth import get_user_model
# from mhcapp.models import AdminProxy, Doctor, Patient, Appointment

# User = get_user_model()  # Use the custom user model

# class NewAppointmentViewTest(TestCase):
#     def setUp(self):
#         # Create a test user and log them in
#         self.client = Client()
#         self.user = User.objects.create_user(
#             phone='1234567890',
#             name='Admin User',
#             role='admin',
#             password='adminpass',
#         )
#         self.client.login(phone='1234567890', password='adminpass')

#         # Create an admin user (no need for AdminProxy creation if it's a proxy model)
#         self.admin_proxy = AdminProxy.objects.get(pk=self.user.pk)  # Access proxy model via the underlying model

#         # Create a test doctor
#         self.doctor_user = User.objects.create_user(
#             phone='0987654321',
#             name='Doctor User',
#             role='doctor',
#             password='doctorpass',
#         )
#         self.doctor = Doctor.objects.create(user=self.doctor_user)

#         # Define the URL for the view
#         self.url = reverse('newappointment')

    # def test_get_request(self):
    #     # Test GET request to ensure the page loads with the correct context
    #     response = self.client.get(self.url)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, 'newappointment.html')
    #     self.assertIn('admin', response.context)
    #     self.assertIn('doctors', response.context)

    # # Test case for posting valid data
    # def test_post_request_valid_data(self):
    #     # Test POST request with valid appointment data
    #     data = {
    #         'patientName': 'Test Patient',
    #         'patientAge': '30',
    #         'patientGender': 'M',  # Use a single-character value for gender
    #         'patientAddress': '123 Test Street',
    #         'phone': '1111111111',
    #         'appointedDoctor': self.doctor_user.id
    #     }
    #     response = self.client.post(self.url, data)

    #     # Ensure the appointment is created and the user is redirected
    #     self.assertEqual(response.status_code, 302)
    #     self.assertEqual(response.url, reverse('admin_dashboard'))

    #     # Check that the patient and appointment were created
    #     self.assertTrue(Patient.objects.filter(user__name='Test Patient').exists())
    #     self.assertTrue(Appointment.objects.filter(patient__user__name='Test Patient').exists())

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from mhcapp.models import Appointment, Doctor, Patient, VitalsRecord

User = get_user_model()

class VitalsEntryViewTest(TestCase):
    def setUp(self):
        # Create a test client
        self.client = Client()

        # Create a test user (nurse role)
        self.nurse_user = User.objects.create_user(
            phone='1234567890',
            name='Nurse User',
            role='nurse',
            password='nursepass',
        )
        self.client.login(phone='1234567890', password='nursepass')

        # Create a test doctor
        self.doctor_user = User.objects.create_user(
            phone='0987654321',
            name='Doctor User',
            role='doctor',
            password='doctorpass',
        )
        self.doctor = Doctor.objects.create(user=self.doctor_user)
        
        self.patient_user = User.objects.create_user(    # Create a test patient
            phone='1111111111',
            name='Patient User',
            role='patient',
            password='patientpass',
        )
        self.patient = Patient.objects.create(
            user=self.patient_user,
            age=30,  # Add a valid age
            gender='M',  # Add a valid gender
            address='123 Test Street',  # Add a valid address
        )
        
        self.appointment = Appointment.objects.create(    # Create a test appointment
            patient=self.patient,  # Use the Patient instance
            doctor=self.doctor,
            status='pending',
        )

        # Define the URL for the view
        self.url = reverse('vitalsentry') + f'?appointment_id={self.appointment.appointment_id}'

    # def test_get_request(self):
    #     # Test GET request to ensure the page loads with the correct context
    #     response = self.client.get(self.url)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, 'vitalsentry.html')
    #     self.assertIn('appointment', response.context)
    #     self.assertEqual(response.context['appointment'], self.appointment)
    #     self.assertIn('latest_vitals', response.context)

    # def test_post_valid_vitals_entry(self):
    #     # Test POST request with valid vitals data
    #     data = {
    #         'bp-systolic': '120',
    #         'bp-diastolic': '80',
    #         'pulse': '72',
    #         'spo2': '98',
    #         'respiratory': '20',
    #         'temperature': '36.5',
    #         'weight': '75',
    #         'height': '172',
    #         'notes': 'Patient is stable.',
    #         'allergies[]': ['Pollen', 'Dust'],
    #     }

    #     response = self.client.post(self.url, data)
    #     self.assertEqual(response.status_code, 302)  # Redirect after success
    #     self.assertRedirects(response, f'/vitalsentry/?appointment_id={self.appointment.appointment_id}')

    #     # Verify that the vitals record was created
    #     vitals = VitalsRecord.objects.filter(appointment=self.appointment).first()
    #     self.assertIsNotNone(vitals)
    #     self.assertEqual(vitals.systolic_bp, 120)
    #     self.assertEqual(vitals.diastolic_bp, 80)
    #     self.assertEqual(vitals.pulse_rate, 72)
    #     self.assertEqual(vitals.spo2, 98)
    #     self.assertEqual(vitals.respiratory_rate, 20)
    #     self.assertEqual(vitals.temperature, 36.5)
    #     self.assertEqual(vitals.weight, 75.0)
    #     self.assertEqual(vitals.height, 172)
    #     self.assertEqual(vitals.notes, 'Patient is stable.')
    #     self.assertEqual(vitals.allergies, 'Pollen, Dust')

    # def test_invalid_appointment_id(self):
    #     # Test with an invalid appointment ID
    #     invalid_url = reverse('vitalsentry') + '?appointment_id=999'
    #     response = self.client.get(invalid_url)
    #     self.assertEqual(response.status_code, 404)  # Should raise a 404 for invalid appointment ID

    # def test_post_with_missing_fields(self):
    #     # Test POST request with missing fields
    #     data = {
    #         'bp-systolic': '',
    #         'bp-diastolic': '',
    #         'pulse': '',
    #         'spo2': '',
    #         'respiratory': '',
    #         'temperature': '',
    #         'weight': '',
    #         'height': '',
    #         'notes': '',
    #         'allergies[]': [],
    #     }

    #     response = self.client.post(self.url, data)
    #     self.assertEqual(response.status_code, 302)  # Redirect after success
    #     self.assertRedirects(response, f'/vitalsentry/?appointment_id={self.appointment.appointment_id}')

    #     # Verify that a vitals record was still created, with empty fields
    #     vitals = VitalsRecord.objects.filter(appointment=self.appointment).first()
    #     self.assertIsNotNone(vitals)
    #     self.assertIsNone(vitals.systolic_bp)
    #     self.assertIsNone(vitals.diastolic_bp)
    #     self.assertIsNone(vitals.pulse_rate)
    #     self.assertIsNone(vitals.spo2)
    #     self.assertIsNone(vitals.respiratory_rate)
    #     self.assertIsNone(vitals.temperature)
    #     self.assertIsNone(vitals.weight)
    #     self.assertIsNone(vitals.height)
    #     self.assertIsNone(vitals.allergies)

# from django.test import TestCase, Client
# from django.urls import reverse
# from django.contrib.auth import get_user_model
# from mhcapp.models import Appointment, Doctor, Patient, Medication, User

# User = get_user_model()
# class OngoingMedicationViewTest(TestCase):
#     def setUp(self):
#         # Setup code remains unchanged
#         self.client = Client()
#         self.doctor_user = User.objects.create_user(
#             phone='1234567890',
#             name='Doctor User',
#             role='doctor',
#             password='doctorpass'
#         )
#         self.doctor = Doctor.objects.create(user=self.doctor_user)
#         self.patient_user = User.objects.create_user(
#             phone='1111111111',
#             name='Patient User',
#             role='patient',
#             password='patientpass'
#         )
#         self.patient = Patient.objects.create(
#             user=self.patient_user,
#             age=30,
#             gender='M',
#             address='123 Test Street'
#         )
#         self.appointment = Appointment.objects.create(
#             patient=self.patient,
#             doctor=self.doctor,
#             status='pending'
#         )
#         self.url = reverse('ongoingMedication')

#     def test_medication_error_handling(self):
#         # Log in as the assigned doctor
#         self.client.login(phone='1234567890', password='doctorpass')

#         # Simulate an error (e.g., invalid appointment ID)
#         data = {'appointment_id': 999}  # Invalid appointment_id
#         response = self.client.post(self.url, data)
#         self.assertEqual(response.status_code, 302)  # Should redirect
#         self.assertRedirects(response, reverse('doctor_dashboard'))
#         messages = list(response.wsgi_request._messages)
#         self.assertTrue(str(messages[0]).startswith("Error:"))

    # def test_invalid_request_method(self):
        #     # Log in as the doctor
        #     self.client.login(phone='1234567890', password='doctorpass')

        #     # Test with a GET request (invalid method)
        #     response = self.client.get(self.url)
        #     self.assertEqual(response.status_code, 302)  # Should redirect
        #     self.assertRedirects(response, reverse('doctor_dashboard'))
        #     messages = list(response.wsgi_request._messages)
        #     self.assertEqual(str(messages[0]), "Invalid request method.")
    # def test_unauthorized_user(self):
    #     # Log in as a different doctor
    #     other_doctor_user = User.objects.create_user(
    #         phone='2222222222',
    #         name='Other Doctor',
    #         role='doctor',
    #         password='otherdoctorpass'
    #     )
    #     self.client.login(phone='2222222222', password='otherdoctorpass')

    #     # Test with an appointment not assigned to the logged-in doctor
    #     data = {'appointment_id': self.appointment.appointment_id}
    #     response = self.client.post(self.url, data)

    #     # Verify redirection to the doctor dashboard
    #     self.assertEqual(response.status_code, 302)  # Expect a redirection
    #     self.assertEqual(response['Location'], reverse('doctor_dashboard'))  # Verify the redirection URL

    #     # Check the error message
    #     messages = list(response.wsgi_request._messages)
    #     self.assertEqual(str(messages[0]), "You are not authorized to update this appointment.")

    # def test_valid_medication_submission(self):
    #     # Log in as the assigned doctor
    #     self.client.login(phone='1234567890', password='doctorpass')

    #     # Test with valid medications
    #     data = {
    #         'appointment_id': self.appointment.appointment_id,
    #         'medication[]': ['Medication 1', 'Medication 2', '   ']  # Includes an empty string
    #     }
    #     response = self.client.post(self.url, data)
    #     self.assertEqual(response.status_code, 302)  # Should redirect
    #     redirect_url = reverse('drloa') + f'?appointment_id={self.appointment.appointment_id}'
    #     self.assertRedirects(response, redirect_url)
    #     messages = list(response.wsgi_request._messages)
    #     self.assertEqual(str(messages[0]), 'Medications have been updated successfully.')

    #     # Retrieve medications in the order they were created
    #     medications = Medication.objects.filter(appointment=self.appointment).order_by('created_at')

    #     # Verify that only valid medications were saved (empty strings are ignored)
    #     self.assertEqual(medications.count(), 2)
    #     self.assertEqual(medications[0].description, 'Medication 1')
    #     self.assertEqual(medications[1].description, 'Medication 2')

    #     # Verify the appointment's status was updated
    #     self.appointment.refresh_from_db()
    #     self.assertEqual(self.appointment.status, 'in_progress')

from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock, ANY  # Import ANY from unittest.mock
from django.contrib.auth import get_user_model
from mhcapp.models import User, Appointment, Investigation, RadioResult, Patient, Doctor, RadiographerProxy, RadiologyTest, Modality

User = get_user_model()

class PredictDiagnosisViewTest(TestCase):
    def setUp(self):
        # Create a test client
        self.client = Client()

        # Create a test user and log them in
        self.user = User.objects.create_user(phone='1234567890', name='Test User', role='rg', password='testpassword')
        self.client.login(phone='1234567890', password='testpassword')

        # Create a test patient
        self.patient_user = User.objects.create_user(phone='1111111111',name='Test Patient', role='patient', password='patientpassword' )
        self.patient = Patient.objects.create(user=self.patient_user,age=30,gender='M',address='123 Test Street')

        # Create a test doctor
        self.doctor_user = User.objects.create_user(phone='1234567899',name='Doctor User',role='doctor',password='doctorpass')
        self.doctor = Doctor.objects.create(user=self.doctor_user)

        # Create a test radiographer
        self.radiographer_user = User.objects.create_user( phone='1234567888', name='Radiographer User', role='rg', password='radiographerpass' )
        self.radiographer = RadiographerProxy.objects.get(pk=self.radiographer_user.pk)

        # Create a test appointment
        self.appointment = Appointment.objects.create( patient=self.patient, doctor=self.doctor, status='pending' )

        # Create a test Modality
        self.modality = Modality.objects.create(name='X-ray')

        # Create a test RadiologyTest
        self.radiology_test = RadiologyTest.objects.create( name='Chest X-ray (CXR)', modality=self.modality )

        # Create a valid Chest X-ray investigation
        self.investigation = Investigation.objects.create(appointment=self.appointment, investigation_type='radio_sub', investigation_id=self.radiology_test.id, requested_by=self.doctor_user)

        # Create a valid radiology result with an image
        self.radio_result = RadioResult.objects.create(radiographer=self.radiographer, appointment=self.appointment,investigation=self.investigation,report_image='chest-pneumonia.png' )  # Use a valid image path
    
    def test_missing_report_image(self):
        # Delete the existing radiology result for the investigation
        self.radio_result.delete()
        
        # Create a radiology result without a report image
        radio_result_no_image = RadioResult.objects.create(
            radiographer=self.radiographer,  # Assign the radiographer
            appointment=self.appointment,
            investigation=self.investigation,
            report_image=None  # No image provided (use None for missing value)
        )

        # Call the predict_diagnosis view
        response = self.client.get(reverse('predict_diagnosis', args=[self.investigation.id]))
        self.assertEqual(response.status_code, 400)

        # Verify the error message
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error'], 'No radiology image found')

    # @patch('mhcapp.views.predict_chest_xray')
    # def test_valid_prediction(self, mock_predict_chest_xray):
    #     # Mock the prediction function
    #     mock_predict_chest_xray.return_value = {
    #         'Pneumonia': 0.85,
    #         'Normal': 0.10,
    #         'Covid-19': 0.05
    #     }

    #     # Call the predict_diagnosis view
    #     response = self.client.get(reverse('predict_diagnosis', args=[self.investigation.id]))
    #     self.assertEqual(response.status_code, 200)

    #     # Verify the response
    #     response_data = response.json()
    #     self.assertIn('prediction', response_data)
    #     self.assertEqual(response_data['prediction'], {
    #         'Pneumonia': "85.00%",
    #         'Normal': "10.00%",
    #         'Covid-19': "5.00%"
    #     })

    #     # Verify that the mock prediction function was called
    #     mock_predict_chest_xray.assert_called_once_with(
    #         self.radio_result.report_image.path,
    #         'mhcapp\\chest_model\\best_model.pth',
    #         ANY  # Use ANY instead of MagicMock.ANY
    #     )
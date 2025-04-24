import datetime
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils.text import slugify

from .models import ChiefComplain, CurrentDiagnosis, Investigation, LabResult, LabTest, Medication, Modality, Patient, Doctor, AdminProxy, NurseProxy, LabTechProxy, PhysicalExam, PreviousDiagnosis, RadioResult, RadiographerProxy, RadiologyTest, Subtest, TreatmentPlan, User, Appointment, VitalsRecord  # Add other models as needed

import json
from django.core.serializers.json import DjangoJSONEncoder
from django.core.files.storage import FileSystemStorage

import torch
from .predict_chest_xray import predict_chest_xray

# views logic.

def login_view(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        print(f'phone: {phone}, password: {password}')
        
        # Authenticate using phone as username (since we're using phone for auth)
        user = authenticate(request, username=phone, password=password)  # Changed parameter
        print(f'user: {user}')
        
        if user is not None:
            print(f'user detected: {user.role}, logging in...')
            login(request, user)
            
            # Redirect based on role
            if user.role == 'patient':
                print(f'user detected: {user.role}, redirecting to patient_dashboard...')
                return redirect('patient_dashboard')
            elif user.role == 'doctor':
                print(f'user detected: {user.role}, redirecting to doctor_dashboard...')
                return redirect('doctor_dashboard')
            elif user.role == 'admin':
                print(f'user detected: {user.role}, redirecting to admin_dashboard...')
                return redirect('admin_dashboard')
            elif user.role == 'nurse':
                print(f'user detected: {user.role}, redirecting to nursedash...')
                return redirect('nursedash')
            elif user.role == 'labt':
                print(f'user detected: {user.role}, redirecting to techdash...')
                return redirect('techdash')
            elif user.role == 'rg':
                print(f'user detected: {user.role}, redirecting to radiographerdash...')
                return redirect('radiographerdash')

            # Add other roles as needed
        else:
            messages.error(request, 'Invalid phone number or password')
    
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')

def home(request):
    return render(request, "drdash.html")

@login_required
def admin_dashboard(request):
    admin = AdminProxy.objects.get(id=request.user.id)
    admin = AdminProxy.objects.get(id=request.user.id)
    appointments = Appointment.objects.all().order_by('-appointment_date')
    
    context = {
        'user': request.user,
        'admin': admin,
        'appointments': appointments,
        'doctors': Doctor.objects.all(),
        'patients': Patient.objects.all()
    }
    return render(request, 'admindash.html', context)

@login_required
def newappointment(request):
    admin = AdminProxy.objects.get(id=request.user.id)
    doctors = Doctor.objects.all()  # if needed for your dynamic dropdown
    context = {
        'admin': admin,
        'doctors': doctors,
    }

    if request.method == "POST":
        # Process the appointment form here.
        # For example, get data from request.POST, validate, and save to an Appointment model (if defined)
        patient_name = request.POST.get('patientName')
        patient_age = request.POST.get('patientAge')
        patient_gender = request.POST.get('patientGender')
        patient_address = request.POST.get('patientAddress')
        phone = request.POST.get('phone')
        appointed_doctor_id = request.POST.get('appointedDoctor')
        print('New appointment form submitted:')
        print(f'patient_name: {patient_name}, patient_age: {patient_age}, patient_gender: {patient_gender}, patient_address: {patient_address}, phone: {phone}, appointed_doctor_id: {appointed_doctor_id}')
        
         # Create a new patient user with role 'patient'
        # Note: In a production system, you may want to generate a random or a more secure temporary password
        new_patient_user = User.objects.create_user(
            phone=phone,
            name=patient_name,
            role='patient',
            password='patient@123'  # Temporary password
        )
        
        # Create the corresponding Patient record
        new_patient = Patient.objects.create(
            user=new_patient_user,
            age=patient_age,
            gender=patient_gender,
            address=patient_address
        )

        # Retrieve the appointed doctor using the selected doctor ID
        try:
            appointed_doctor_user = User.objects.get(id=appointed_doctor_id)
            appointed_doctor = Doctor.objects.get(user=appointed_doctor_user)
        except (User.DoesNotExist, Doctor.DoesNotExist):
            # Handle error appropriately. Here, we simply redirect back with an error message.
            return redirect('admin_dashboard')
        
        # Create the appointment record
        appointment = Appointment.objects.create(
            patient=new_patient,
            doctor=appointed_doctor,
            status='pending'
            # You can add chief_complain, physical_exam, etc. here if your form collects that data.
        )
        print(f'Appointment created with id: {appointment.appointment_id}')
        return redirect('admin_dashboard')
    return render(request, "newappointment.html", context)

@login_required
def nursedash(request):
    # Get the nurse instance from the proxy model
    nurse = NurseProxy.objects.get(id=request.user.id)
    
    # Retrieve pending appointments ordered by appointment_date (newest first)
    pending_appointments = Appointment.objects.filter(status='pending').order_by('-appointment_date')
    print(f'Pending appointments: {pending_appointments}')
    # Optionally, you can still pass patients if needed elsewhere in your template
    patients = Patient.objects.all()
    
    context = {
        'user': request.user,
        'nurse': nurse,
        'patients': patients,
        'pending_appointments': pending_appointments,
    }
    return render(request, "nursedash.html", context)

@login_required
def vitalsentry(request):
    # Retrieve the appointment_id from the GET parameters or form data
    appointment_id = request.GET.get('appointment_id') or request.POST.get('appointment_id')
    print(f'Appointment ID: {appointment_id}')
    if not appointment_id:
        messages.error(request, "No appointment specified. Please select an appointment.")
        return redirect('nursedash')  # Redirect to nurse dashboard if no appointment_id
    
    # Retrieve the appointment object (or return 404 if not found)
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
    print(f'Appointment: {appointment}')
    
    # Handle form submission
    if request.method == 'POST':
        print('Vitals form submitted')
        try:
            # Properly convert form values to appropriate types
            systolic_bp = request.POST.get('bp-systolic')
            diastolic_bp = request.POST.get('bp-diastolic')
            pulse_rate = request.POST.get('pulse')
            spo2 = request.POST.get('spo2')
            respiratory_rate = request.POST.get('respiratory')
            temperature = request.POST.get('temperature')
            weight = request.POST.get('weight')
            height = request.POST.get('height')
            notes = request.POST.get('notes')
            
            # Convert values to appropriate types, handling empty strings
            systolic_bp = int(systolic_bp) if systolic_bp else None
            diastolic_bp = int(diastolic_bp) if diastolic_bp else None
            pulse_rate = int(pulse_rate) if pulse_rate else None
            spo2 = int(spo2) if spo2 else None
            respiratory_rate = int(respiratory_rate) if respiratory_rate else None
            temperature = float(temperature) if temperature else None
            weight = float(weight) if weight else None
            height = int(height) if height else None
            
            # Handle allergies (multiple select)
            allergies = request.POST.getlist('allergies[]')
            allergies_str = ", ".join(allergies) if allergies else None
            
            # Create a new vitals record
            vitals = VitalsRecord(
                appointment=appointment,
                systolic_bp=systolic_bp,
                diastolic_bp=diastolic_bp,
                pulse_rate=pulse_rate,
                spo2=spo2,
                respiratory_rate=respiratory_rate,
                temperature=temperature,
                weight=weight,
                height=height,
                notes=notes,
                allergies=allergies_str,
                entered_by=request.user
            )
            
            # Calculate and set BMI if height and weight are provided
            if height and weight and height > 0:
                height_in_meters = height / 100
                bmi = round(weight / (height_in_meters ** 2), 1)
                vitals.bmi = bmi
            
            print('Saving vitals record to database...')
            vitals.save()
            print(f'Vitals record saved with ID: {vitals.id}')
            
            # Also update patient record if height/weight/allergies data is present
            patient = appointment.patient
            update_patient = request.POST.get('update_patient_data') == 'on'
            
            if update_patient:
                if height:
                    patient.height = height
                
                if weight:
                    patient.weight = weight
                
                if allergies_str:
                    patient.allergies = allergies_str
                    
                patient.save()
                print(f'Patient record updated')
            
            messages.success(request, "Vitals recorded successfully!")
            
            # Redirect to the same page to prevent form resubmission
            return redirect(f'/vitalsentry/?appointment_id={appointment_id}')
            
        except Exception as e:
            print(f"Error saving vitals: {str(e)}")
            messages.error(request, f"Error saving vitals: {str(e)}")
    
    # Get previous vitals for this patient
    try:
        previous_vitals = VitalsRecord.objects.filter(
            appointment__patient=appointment.patient
        ).order_by('-created_at')[:10]  # Get the 10 most recent records
        
        # Get the latest vitals record for this patient
        latest_vitals = previous_vitals.first() if previous_vitals.exists() else None
        
        # If there's no previous record but there's patient data, pre-fill with patient data
        if not latest_vitals and appointment.patient:
            patient = appointment.patient
            latest_vitals = VitalsRecord(
                appointment=appointment,
                height=patient.height if hasattr(patient, 'height') else None,
                weight=patient.weight if hasattr(patient, 'weight') else None,
                allergies=patient.allergies if hasattr(patient, 'allergies') else None
            )
            
            # Calculate BMI if height and weight are available
            if latest_vitals.height and latest_vitals.weight and latest_vitals.height > 0:
                height_in_meters = latest_vitals.height / 100
                latest_vitals.bmi = round(latest_vitals.weight / (height_in_meters ** 2), 1)
                
    except Exception as e:
        print(f"Error fetching previous vitals: {str(e)}")
        previous_vitals = []
        latest_vitals = None
    
    # Get all appointment history for this patient
    patient_appointments = Appointment.objects.filter(
        patient=appointment.patient
    ).exclude(
        appointment_id=appointment_id  # Exclude the current appointment
    ).order_by('-appointment_date')[:5]  # Get the 5 most recent appointments
    
    # Format allergies as a list if present
    if latest_vitals and latest_vitals.allergies:
        allergies_list = [allergy.strip() for allergy in latest_vitals.allergies.split(',')]
        latest_vitals.allergies_list = allergies_list
    
    # Prepare context for the template
    context = {
        'appointment': appointment,
        'patient': appointment.patient,
        'doctor': appointment.doctor,
        'previous_vitals': previous_vitals,
        'latest_vitals': latest_vitals,
        'appointment_id': appointment_id,
        'patient_appointments': patient_appointments,
        'current_datetime': datetime.datetime.now(),
        'current_user': request.user,
    }
    
    return render(request, "vitalsentry.html", context)

@login_required
def doctor_dashboard(request):
    try:
        # Get the doctor object
        doctor = Doctor.objects.get(user=request.user)
        print(f'Doctor: {doctor}')
        
        # Count new/pending appointments for this doctor
        new_appointments_count = Appointment.objects.filter(
            doctor=doctor, 
            status='pending'
        ).count()
        print(f'New appointments count: {new_appointments_count}')
        
        # Get total appointments for this doctor
        total_appointments_count = Appointment.objects.filter(doctor=doctor).count()
        print(f'Total appointments count: {total_appointments_count}')
        
        # Get recovered patients count (assuming you mark appointments as 'completed' when recovered)
        recovered_patients_count = Appointment.objects.filter(
            doctor=doctor, 
            status='completed'
        ).count()
        print(f'Recovered patients count: {recovered_patients_count}')
        
        # Get referred patients count (assuming you have a 'referred' status in appointments)
        referred_patients_count = Appointment.objects.filter(
            doctor=doctor, 
            status='referred'
        ).count()
        print(f'Referred patients count: {referred_patients_count}')
        
        # Get pending appointments for this doctor - renamed from new_appointments to match template
        pending_appointments = Appointment.objects.filter(
            doctor=doctor,
            # status='pending'
        ).select_related('patient', 'patient__user').order_by('-appointment_date')[:10]
        print(f'Pending appointments: {pending_appointments}')
        
        # Current date and time information
        current_datetime = datetime.datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        
        context = {
            # User and doctor info
            'user': request.user,
            'doctor': doctor,
            
            # Counts for dashboard cards
            'new_appointments_count': new_appointments_count,
            'total_appointments_count': total_appointments_count,
            'recovered_patients_count': recovered_patients_count,
            'referred_patients_count': referred_patients_count,
            
            # Appointments for table
            'pending_appointments': pending_appointments,
            
            # DateTime information
            'today': current_datetime,
            'current_hour': current_datetime.hour,
            
            # URL for the "View Patient" button
            'drloa_url': reverse('drloa'),
        }
        return render(request, 'drdash.html', context)
    except Doctor.DoesNotExist:
        messages.error(request, 'Doctor profile not found')
        return redirect('login')
    except Exception as e:
        messages.error(request, f'Error accessing dashboard: {str(e)}')
        return redirect('login')

# Update both views to handle the appointment_id parameter
@login_required
def drloa(request):
    appointment_id = request.GET.get('appointment_id')
    
    try:
        if appointment_id:
            # Get the appointment object
            appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
            latest_vitals = VitalsRecord.objects.filter(appointment=appointment).order_by('-created_at').first()
            ongoingMedication = Medication.objects.filter(appointment=appointment)
            ongoingMedicationUpdateTime = ongoingMedication.latest('created_at').created_at if ongoingMedication.exists() else None
            previousDiagnosis = PreviousDiagnosis.objects.filter(appointment=appointment)
            previousDiagnosisUpdateTime = previousDiagnosis.latest('created_at').created_at if previousDiagnosis.exists() else None
            physical_exam = PhysicalExam.objects.filter(appointment=appointment).first()  # Retrieve as a single object
            chiefComplains = ChiefComplain.objects.filter(appointment=appointment)
            chiefComplainUpdateTime = chiefComplains.latest('created_at').created_at if chiefComplains.exists() else None
            currentDiagnosis = CurrentDiagnosis.objects.filter(appointment=appointment)
            currentDiagnosisUpdateTime = currentDiagnosis.latest('created_at').created_at if currentDiagnosis.exists() else None
            treatmentPlans = TreatmentPlan.objects.filter(appointment=appointment)
            treatmentPlanUpdateTime = treatmentPlans.latest('created_at').created_at if treatmentPlans.exists() else None
            
            # Fetch individual tests and test groups
            labtest_subsets = Subtest.objects.all()
            labtest_groups = LabTest.objects.all()
            radiotest_subsets = RadiologyTest.objects.all()
            radiotest_groups = Modality.objects.all()
            
            # Build the investigations list
            investigations = []

            for group in labtest_groups:
                investigations.append({
                    "id": group.id,
                    "type": "lab_group",
                    "name": group.name
                })

            for subtest in labtest_subsets:
                investigations.append({
                    "id": subtest.id,
                    "type": "lab_sub",
                    "name": f"{subtest.name} ({subtest.test.name})"
                })

            for group in radiotest_groups:
                investigations.append({
                    "id": group.id,
                    "type": "radio_group",
                    "name": group.name
                })

            for test in radiotest_subsets:
                investigations.append({
                    "id": test.id,
                    "type": "radio_sub",
                    "name": f"{test.name} ({test.modality.name})"
                })
            print(f'investigations just before request from drloa views: ')
            requested_investigations = Investigation.objects.filter(appointment=appointment)
            print(f'requested_investigations from drloa views: {requested_investigations}')
            context = {
                'appointment': appointment,
                'patient': appointment.patient,
                'doctor': appointment.doctor,
                'current_datetime': datetime.datetime.now(),
                'latest_vitals': latest_vitals,
                'ongoingMedication': ongoingMedication,
                'ongoingMedicationUpdateTime': ongoingMedicationUpdateTime,
                'previousDiagnosis': previousDiagnosis,
                'previousDiagnosisUpdateTime': previousDiagnosisUpdateTime,
                'physical_exam': physical_exam,
                'chiefComplains': chiefComplains,
                'chiefComplainUpdateTime': chiefComplainUpdateTime,
                'currentDiagnosis': currentDiagnosis,
                'currentDiagnosisUpdateTime': currentDiagnosisUpdateTime,
                'treatmentPlans': treatmentPlans,
                'treatmentPlanUpdateTime': treatmentPlanUpdateTime,
                'labtest_groups': labtest_groups,
                'labtest_subsets': labtest_subsets,
                'radiotest_groups': radiotest_groups,
                'radiotest_subsets': radiotest_subsets,
                'investigations': json.dumps(investigations, cls=DjangoJSONEncoder),
                'requested_investigations': requested_investigations,
            }
        else:
            context = {
                'error_message': 'No appointment ID provided',
                'current_datetime': datetime.datetime.now(),
            }
        print("rendering with context drLOA.html")
        return render(request, "drLOA.html", context)
    except Exception as e:
        context = {
            'error_message': str(e),
            'current_datetime': datetime.datetime.now(),
        }
        print(f'Error fetching appointment: {str(e)}')
        return render(request, "drLOA.html", context)

def loa(request):
    if request.method == 'POST':
        appointment_id = request.POST.get('appointment_id')

        # Process submitted medications
        medications = request.POST.getlist('medication[]')
        print(f'LOA form submitted: appointment_id: {appointment_id}, loa_notes: {medications}')
        
        
        messages.success(request, 'LOA saved successfully!')
        return redirect('doctor_dashboard')
    return render(request, "loa.html")


@login_required
def ongoingMedication(request):
    """Handle the submission of medication form data"""
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('doctor_dashboard')

    try:
        appointment_id = request.POST.get('appointment_id')
        if not appointment_id:
            messages.error(request, "Appointment ID is required.")
            return redirect('doctor_dashboard')
        
        appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
        
        # Verify the logged-in user is the assigned doctor
        if request.user != appointment.doctor.user:
            messages.error(request, "You are not authorized to update this appointment.")
            return redirect('doctor_dashboard')

        # Process submitted medications
        medications = request.POST.getlist('medication[]')
        
        # Remove existing medications for this appointment
        Medication.objects.filter(appointment=appointment).delete()
        
        # Create new medication records
        for med in medications:
            if med.strip():  # Only save non-empty entries
                Medication.objects.create(
                    appointment=appointment,
                    description=med.strip(),
                    created_by=request.user
                )
        # Save the medication to the database
        appointment.status = 'in_progress'
        appointment.save()

        print(f'Medications saved for appointment ID: {appointment_id}')
        messages.success(request, 'Medications have been updated successfully.')

        # Generate the URL with the query parameter
        redirect_url = reverse('drloa') + f'?appointment_id={appointment_id}'
        return HttpResponseRedirect(redirect_url)

    except Exception as e:
        print(f"Error saving medications: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('doctor_dashboard')


@login_required
def previousDiagnosis(request):
    """Handle the submission of previous diagnosis form data"""
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('doctor_dashboard')

    try:
        appointment_id = request.POST.get('appointment_id')
        print(f'appointment_id from previous diagnosis: {appointment_id}')
        if not appointment_id:
            messages.error(request, "Appointment ID is required.")
            return redirect('doctor_dashboard')
        
        appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
        
        # Verify the logged-in user is the assigned doctor
        if request.user != appointment.doctor.user:
            messages.error(request, "You are not authorized to update this appointment.")
            return redirect('doctor_dashboard')

        # Process submitted diagnoses
        diagnoses = request.POST.getlist('previous_diagnosis[]')
        print(f'diagnoses recieved from previous diagnosis: {diagnoses}')
        # Remove existing diagnoses for this appointment
        PreviousDiagnosis.objects.filter(appointment=appointment).delete()
        
        # Create new diagnosis records
        for diag in diagnoses:
            if diag.strip():  # Only save non-empty entries
                PreviousDiagnosis.objects.create(
                    appointment=appointment,
                    description=diag.strip(),
                    created_by=request.user
                )

        appointment.status = 'in_progress'
        appointment.save()

        print(f'Diagnoses saved for appointment ID: {appointment_id}')
        messages.success(request, 'Previous diagnoses have been updated successfully.')

        # Generate the URL with the query parameter
        redirect_url = reverse('drloa') + f'?appointment_id={appointment_id}'
        return HttpResponseRedirect(redirect_url)

    except Exception as e:
        print(f"Error saving diagnoses: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('doctor_dashboard')

@login_required
def physicalExam(request):
    appointment_id = request.POST.get('appointment_id')
    print(f'appointment_id from physical exam: {appointment_id}')
    
    if appointment_id:
        appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
        physical_exam, created = PhysicalExam.objects.get_or_create(appointment=appointment, defaults={'created_by': request.user})
        
        if request.method == 'POST':
            print('Physical exam form submitted')
            physical_exam.general = request.POST.get('general')
            physical_exam.cns = request.POST.get('cns')
            physical_exam.cvs = request.POST.get('cvs')
            physical_exam.rs = request.POST.get('rs')
            physical_exam.abdomen = request.POST.get('abdomen')
            physical_exam.extremities = request.POST.get('extremities')
            physical_exam.save()
            print('Physical exam saved successfully')
            
            # Save the appointment status as 'in_progress' if not already set
            appointment.status = 'physical examined'
            appointment.save()
            messages.success(request, 'Physical exam saved successfully')
            return redirect(f'/drloa/?appointment_id={appointment_id}')
        
        context = {
            'appointment': appointment,
            'physical_exam': physical_exam,
        }
    else:
        context = {
            'error_message': 'No appointment ID provided',
        }
    
    return render(request, "drLOA.html", context)

@login_required
def chiefComplain(request):
    """Handle the submission of chief complain form data"""
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('doctor_dashboard')

    try:
        appointment_id = request.POST.get('appointment_id')
        if not appointment_id:
            messages.error(request, "Appointment ID is required.")
            return redirect('doctor_dashboard')
        
        appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
        
        # Verify the logged-in user is the assigned doctor
        if request.user != appointment.doctor.user:
            messages.error(request, "You are not authorized to update this appointment.")
            return redirect('doctor_dashboard')

        # Process submitted chief complains
        chief_complains = request.POST.getlist('chief_complain[]')
        
        # Remove existing chief complains for this appointment
        ChiefComplain.objects.filter(appointment=appointment).delete()
        
        # Create new chief complain records
        for complain in chief_complains:
            if complain.strip():  # Only save non-empty entries
                ChiefComplain.objects.create(
                    appointment=appointment,
                    description=complain.strip(),
                    created_by=request.user
                )
        print(f'Chief complains saved for appointment ID: {appointment_id}')
        # Save the appointment status as 'in_progress' if not already set
        appointment.status = 'in_progress'
        appointment.save()
        
        messages.success(request, 'Chief complains have been updated successfully.')

        # Generate the URL with the query parameter
        redirect_url = reverse('drloa') + f'?appointment_id={appointment_id}'
        return HttpResponseRedirect(redirect_url)

    except Exception as e:
        print(f"Error saving chief complains: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('doctor_dashboard')
    
@login_required
def request_investigation(request):
    appointment_id = request.POST.get('appointment_id')
    investigation_id = request.POST.get('investigation_id')
    investigation_type = request.POST.get('investigation_type')
    print("Investigation request form submitted successfully")
    print(f'appointment_id: {appointment_id}, investigation_id: {investigation_id}, investigation_type: {investigation_type}')
    if appointment_id and investigation_id and investigation_type:
        appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
        Investigation.objects.create(
            appointment=appointment,
            investigation_type=investigation_type,
            investigation_id=investigation_id,
            requested_by=request.user
        )
        messages.success(request, 'Investigation requested successfully')
        
        # Save the appointment status as 'in_progress' if not already set
        appointment.status = 'requested'
        appointment.save()

        return redirect(f'/drloa/?appointment_id={appointment_id}')
    else:
        messages.error(request, 'Failed to request investigation')
        return redirect(f'/drloa/?appointment_id={appointment_id}')
    
@login_required
def cancel_investigation(request, investigation_id):
    investigation = get_object_or_404(Investigation, pk=investigation_id)
    investigation.status = 'canceled'
    investigation.save()
    return redirect(f'/drloa/?appointment_id={investigation.appointment.appointment_id}')


@login_required
def view_investigation(request, investigation_id):
    investigation = get_object_or_404(Investigation, pk=investigation_id)
    radio_result = RadioResult.objects.filter(appointment=investigation.appointment, investigation_id=investigation.id).first()
    lab_results = LabResult.objects.filter(investigation=investigation)
    patient = investigation.appointment.patient
    doctor = investigation.appointment.doctor
    appointment = investigation.appointment
    latest_vitals = VitalsRecord.objects.filter(appointment=appointment).order_by('-created_at').first()
    print(f'laboratory results from view_investigation views: {lab_results}')
    return render(request, 'view_investigation.html', {
        'investigation': investigation,
        'radio_result': radio_result,
        'lab_results': lab_results,
        'patient': patient,
        'doctor': doctor,
        'latest_vitals': latest_vitals,
    })

@login_required
def predict_diagnosis(request, investigation_id):
    investigation = get_object_or_404(Investigation, pk=investigation_id)
    if investigation.get_name() != 'Chest X-ray (CXR)':
        return JsonResponse({'error': 'Invalid investigation type'}, status=400)

    radio_result = RadioResult.objects.filter(appointment=investigation.appointment, investigation_id=investigation.id).first()
    if not radio_result or not radio_result.report_image:
        return JsonResponse({'error': 'No radiology image found'}, status=400)

    # Define the paths
    image_path = radio_result.report_image.path  # Path to the image file
    model_path = 'mhcapp\\chest_model\\best_model.pth'  # Update this path to the trained model file
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Run the prediction
    prediction = predict_chest_xray(image_path, model_path, device)
    
    # Sort predictions by probability and get the top 5
    top_predictions = sorted(prediction.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Convert probabilities to percentages
    top_predictions = {label: f"{prob * 100:.2f}%" for label, prob in top_predictions}
    
    return JsonResponse({'prediction': top_predictions})

@login_required
def currentDiagnosis(request):
    """Handle the submission of current diagnosis form data"""
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('doctor_dashboard')

    try:
        appointment_id = request.POST.get('appointment_id')
        if not appointment_id:
            messages.error(request, "Appointment ID is required.")
            return redirect('doctor_dashboard')
        
        appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
        
        # Verify the logged-in user is the assigned doctor
        if request.user != appointment.doctor.user:
            messages.error(request, "You are not authorized to update this appointment.")
            return redirect('doctor_dashboard')

        # Process submitted diagnoses
        diagnoses = request.POST.getlist('diagnosis[]')
        
        # Remove existing diagnoses for this appointment
        CurrentDiagnosis.objects.filter(appointment=appointment).delete()
        
        # Create new diagnosis records
        for diag in diagnoses:
            if diag.strip():  # Only save non-empty entries
                CurrentDiagnosis.objects.create(
                    appointment=appointment,
                    description=diag.strip(),
                    created_by=request.user
                )
        print(f'Diagnoses saved for appointment ID: {appointment_id}')

        # Save the appointment status as 'in_progress' if not already set
        appointment.status = 'diagnosed'
        appointment.save()

        messages.success(request, 'Current diagnoses have been updated successfully.')

        # Generate the URL with the query parameter
        redirect_url = reverse('drloa') + f'?appointment_id={appointment_id}'
        return HttpResponseRedirect(redirect_url)

    except Exception as e:
        print(f"Error saving diagnoses: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('doctor_dashboard')
    
@login_required
def treatmentPlan(request):
    """Handle the submission of treatment plan form data"""
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('doctor_dashboard')

    try:
        appointment_id = request.POST.get('appointment_id')
        if not appointment_id:
            messages.error(request, "Appointment ID is required.")
            return redirect('doctor_dashboard')
        
        appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
        
        # Verify the logged-in user is the assigned doctor
        if request.user != appointment.doctor.user:
            messages.error(request, "You are not authorized to update this appointment.")
            return redirect('doctor_dashboard')

        # Process submitted treatment plans
        treatment_plans = request.POST.getlist('treatment_plan[]')
        
        # Remove existing treatment plans for this appointment
        TreatmentPlan.objects.filter(appointment=appointment).delete()
        
        # Create new treatment plan records
        for plan in treatment_plans:
            if plan.strip():  # Only save non-empty entries
                TreatmentPlan.objects.create(
                    appointment=appointment,
                    description=plan.strip(),
                    created_by=request.user
                )
        # Save the treatment plan to the database
        appointment.status = 'Prescribed'
        appointment.save()


        print(f'Treatment plans saved for appointment ID: {appointment_id}')
        messages.success(request, 'Treatment plans have been updated successfully.')

        # Generate the URL with the query parameter
        redirect_url = reverse('drloa') + f'?appointment_id={appointment_id}'
        return HttpResponseRedirect(redirect_url)

    except Exception as e:
        print(f"Error saving treatment plans: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('doctor_dashboard')

@login_required
def radiographerdash(request):
    rg = RadiographerProxy.objects.get(id=request.user.id)
    investigations = Investigation.objects.filter(investigation_type='radio_sub').order_by('-requested_at')
    print(f'investigations from radiographerdash views: {investigations}')
    
    context = {
        'user': request.user,
        'rg': rg,
        'investigations': investigations,
    }
    return render(request, "radiographerdash.html", context)

def radnewreq(request, investigation_id):
    rg = RadiographerProxy.objects.get(id=request.user.id)
    investigation = get_object_or_404(Investigation, pk=investigation_id)
    radio_test_id = investigation.investigation_id
    radio_test= RadiologyTest.objects.get(id=investigation.investigation_id)
    radio_result, created = RadioResult.objects.get_or_create(investigation_id=investigation_id,appointment_id=investigation.appointment_id, defaults={'radiographer': rg})
    print(f'radio_test_name from radnewreq: {radio_test.name}')
    context = {
        'investigation': investigation,
        'radio_test_name': radio_test,
        'rg': rg,
        'radio_result': radio_result
    }
    return render(request, "radnewreq.html", context)

@login_required
def upload_report(request, investigation_id):
    investigation = get_object_or_404(Investigation, pk=investigation_id)
    if request.method == 'POST' and request.FILES.get('report_image'):
        report_image = request.FILES['report_image']
        
        # Construct the new filename
        patient_name = slugify(investigation.appointment.patient.user.name)
        doctor_name = slugify(investigation.appointment.doctor.user.name)
        appointment_id = investigation.appointment.appointment_id
        new_filename = f"{patient_name}_{doctor_name}_{appointment_id}_{investigation_id}.{report_image.name.split('.')[-1]}"
        
        # Save the file with the new name
        fs = FileSystemStorage()
        filename = fs.save(new_filename, report_image)
        uploaded_file_url = fs.url(filename)
        
        # Save the file URL or path to the RadioResult model
        radiographer = RadiographerProxy.objects.get(id=request.user.id)
        radio_result, created = RadioResult.objects.get_or_create(
            radiographer=radiographer,
            appointment=investigation.appointment,
            investigation_id=investigation_id,
            defaults={'report_image': filename}
        )
        if not created:
            radio_result.report_image.delete(save=False)  # Delete the old image
            radio_result.report_image = filename
            radio_result.save()
        
        # Set the investigation status to completed
        investigation.status = 'completed'
        investigation.save()

        return redirect('radiographerdash')
    return render(request, "radnewreq.html", {'investigation': investigation})

@login_required
def techdash(request):
    labtech = LabTechProxy.objects.get(id=request.user.id)
    
    # Filter investigations to include only 'lab_group' and 'lab_sub' types
    investigations = Investigation.objects.filter(investigation_type__in=['lab_group', 'lab_sub'])
    
    context = {
        'user': request.user,
        'labtech': labtech,
        'investigations': investigations,
    }
    return render(request, "techdash.html", context)


def techreqdetails(request, investigation_id):
    investigation = get_object_or_404(Investigation, pk=investigation_id)
    
    # Determine the subtests to display
    if investigation.investigation_type in ['lab_group', 'lab_sub']:
        if investigation.investigation_type == 'lab_group':
            subtests = Subtest.objects.filter(test__id=investigation.investigation_id)
        else:
            subtests = Subtest.objects.filter(id=investigation.investigation_id)
    else:
        subtests = []

    # Retrieve existing LabResult entries for the investigation
    existing_results = {result.test_name: result.result for result in LabResult.objects.filter(investigation=investigation)}

    if request.method == 'POST':
        # Delete previous LabResult entries for this investigation
        LabResult.objects.filter(investigation=investigation).delete()

        for subtest in subtests:
            result = request.POST.get(f'result_{subtest.id}')
            reference = f"Male: {subtest.male_normal_low} - {subtest.male_normal_high} {subtest.unit}, Female: {subtest.female_normal_low} - {subtest.female_normal_high} {subtest.unit}"
            LabResult.objects.create(
                investigation=investigation,
                test_name=subtest.name,
                result=result,
                reference=reference,
                entered_by=request.user
            )
        # Set the investigation status to completed
        investigation.status = 'completed'
        investigation.save()
        return redirect('/techdash/') 

    context = {
        'investigation': investigation,
        'subtests': subtests,
        'existing_results': existing_results,
    }
    return render(request, "techreqdetails.html", context)


@login_required
def patient_dashboard(request):
    try:
        # Get the patient object associated with the logged-in user
        patient = Patient.objects.get(user=request.user)
        print(f'patient gender is {patient.gender} from patient_dashboard views')
        isMale = True if patient.gender=='M' else False
        # Get all appointments for this patient, ordered by latest first
        appointments = Appointment.objects.filter(patient=patient).order_by('-appointment_date')
        
        # Get the latest vitals record for this patient
        latest_vitals = VitalsRecord.objects.filter(
            appointment__patient=patient
        ).order_by('-created_at').first()
        
        # Calculate current hour for greeting (Django templates can handle time conditionals,
        # but we're providing the hour here for robustness)
        current_datetime = datetime.datetime.now()
        current_hour = current_datetime.hour
        
        # Prepare context for template rendering
        context = {
            'user': request.user,
            'patient': patient,
            'appointments': appointments,
            'latest_vitals': latest_vitals,
            'today': current_datetime,
            'current_hour': current_hour,
            'isMale': isMale,
        }
        
        return render(request, 'patientdash.html', context)
        
    except Patient.DoesNotExist:
        messages.error(request, 'Patient profile not found')
        return redirect('login')
    except Exception as e:
        messages.error(request, f'Error accessing dashboard: {str(e)}')
        return redirect('login')
    
@login_required
def view_patient_appointment(request, appointment_id):
    try:
        # Get the appointment with the specified ID
        appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
        
        # Check if the logged-in user is the patient for this appointment (security check)
        if appointment.patient.user != request.user:
            messages.error(request, "You don't have permission to view this appointment")
            return redirect('patient_dashboard')
        
        # Get vital signs for this appointment
        latest_vitals = VitalsRecord.objects.filter(appointment=appointment).order_by('-created_at').first()
        
        # Get all medical data for this appointment
        ongoingMedication = Medication.objects.filter(appointment=appointment)
        previousDiagnosis = PreviousDiagnosis.objects.filter(appointment=appointment)
        physical_exam = PhysicalExam.objects.filter(appointment=appointment).first()
        chiefComplains = ChiefComplain.objects.filter(appointment=appointment)
        currentDiagnosis = CurrentDiagnosis.objects.filter(appointment=appointment)
        treatmentPlans = TreatmentPlan.objects.filter(appointment=appointment)
        
        # Get investigations for this appointment
        requested_investigations = Investigation.objects.filter(appointment=appointment)
        
        # Create a list of completed investigations with their results
        completed_investigations = []
        for investigation in requested_investigations:
            if investigation.status == 'completed':
                if investigation.investigation_type in ['lab_group', 'lab_sub']:
                    # Get lab results
                    lab_results = LabResult.objects.filter(investigation=investigation)
                    if lab_results.exists():
                        completed_investigations.append({
                            'investigation': investigation,
                            'results': lab_results,
                            'type': 'lab'
                        })
                elif investigation.investigation_type in ['radio_group', 'radio_sub']:
                    # Get radiology results
                    radio_result = RadioResult.objects.filter(investigation=investigation).first()
                    if radio_result:
                        completed_investigations.append({
                            'investigation': investigation,
                            'result': radio_result,
                            'type': 'radiology'
                        })
        
        context = {
            'appointment': appointment,
            'patient': appointment.patient,
            'doctor': appointment.doctor,
            'current_datetime': datetime.datetime.now(),
            'latest_vitals': latest_vitals,
            'ongoingMedication': ongoingMedication,
            'previousDiagnosis': previousDiagnosis,
            'physical_exam': physical_exam,
            'chiefComplains': chiefComplains,
            'currentDiagnosis': currentDiagnosis,
            'treatmentPlans': treatmentPlans,
            'requested_investigations': requested_investigations,
            'completed_investigations': completed_investigations,
        }
        
        return render(request, 'myappointmentdetails.html', context)
    
    except Exception as e:
        messages.error(request, f"Error accessing appointment details: {str(e)}")
        return redirect('patient_dashboard')
    
@login_required
def view_my_investigation(request, investigation_id):
    investigation = get_object_or_404(Investigation, pk=investigation_id)
    radio_result = RadioResult.objects.filter(appointment=investigation.appointment, investigation_id=investigation.id).first()
    lab_results = LabResult.objects.filter(investigation=investigation)
    patient = investigation.appointment.patient
    doctor = investigation.appointment.doctor
    appointment = investigation.appointment
    latest_vitals = VitalsRecord.objects.filter(appointment=appointment).order_by('-created_at').first()
    print(f'laboratory results from view_investigation views: {lab_results}')
    return render(request, 'viewmyinvestigation.html', {
        'investigation': investigation,
        'radio_result': radio_result,
        'lab_results': lab_results,
        'patient': patient,
        'doctor': doctor,
        'latest_vitals': latest_vitals,
    })
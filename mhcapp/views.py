import datetime
from django.http import HttpResponseRedirect
from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.contrib.auth import authenticate, login 
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import ChiefComplain, CurrentDiagnosis, Medication, Patient, Doctor, AdminProxy, NurseProxy, LabTechProxy, PreviousDiagnosis, RadiographerProxy, TreatmentPlan, User, Appointment, VitalsRecord  # Add other models as needed

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


def home(request):
    return render(request, "drdash.html")



# def admindash(request):
#     return render(request, "admindash.html")

def radnewreq(request):
    return render(request, "radnewreq.html")


@login_required
def patient_dashboard(request):
    try:
        patient = Patient.objects.get(user=request.user)
        context = {
            'user': request.user,
            'patient': patient,
            # 'appointments': patient.appointment_set.all(),
            # 'medical_records': patient.medicalrecord_set.all()
        }
        return render(request, 'patientdash.html', context)
    except Patient.DoesNotExist:
        messages.error(request, 'Patient profile not found')
        return redirect('login')
    except Exception as e:
        messages.error(request, f'Error accessing dashboard: {str(e)}')
        return redirect('home')

def techreqdetails(request):
    return render(request, "techreqdetails.html")

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
            status='pending'
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
def techdash(request):
    labtech = LabTechProxy.objects.get(id=request.user.id)
    context = {
        'user': request.user,
        'labtech': labtech,
        # 'techreqs': TechReq.objects.all()
    }
    return render(request, "techdash.html", context)

@login_required
def radiographerdash(request):
    rg = RadiographerProxy.objects.get(id=request.user.id)
    context = {
        'user': request.user,
        'rg': rg,
        # 'radreqs': RadReq.objects.all()
    }
    return render(request, "radiographerdash.html", context)


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
            chiefComplains = ChiefComplain.objects.filter(appointment=appointment)
            chiefComplainUpdateTime = chiefComplains.latest('created_at').created_at if chiefComplains.exists() else None
            currentDiagnosis = CurrentDiagnosis.objects.filter(appointment=appointment)
            currentDiagnosisUpdateTime = currentDiagnosis.latest('created_at').created_at if currentDiagnosis.exists() else None
            treatmentPlans = TreatmentPlan.objects.filter(appointment=appointment)
            treatmentPlanUpdateTime = treatmentPlans.latest('created_at').created_at if treatmentPlans.exists() else None
            print(f'Appointment: {appointment}')
            print(f'ongoingMedication: {ongoingMedication}')
            print(f'previousDiagnosis of the patient before context: {previousDiagnosis}')
            print(f'chiefComplains: {chiefComplains}')
            print(f'currentDiagnosis: {currentDiagnosis}')
            print(f'treatmentPlans: {treatmentPlans}')
            
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
                'chiefComplains': chiefComplains,
                'chiefComplainUpdateTime': chiefComplainUpdateTime,
                'currentDiagnosis': currentDiagnosis,
                'currentDiagnosisUpdateTime': currentDiagnosisUpdateTime,
                'treatmentPlans': treatmentPlans,
                'treatmentPlanUpdateTime': treatmentPlanUpdateTime,
            }
        else:
            context = {
                'error_message': 'No appointment ID provided',
                'current_datetime': datetime.datetime.now(),
            }
        
        return render(request, "drLOA.html", context)
    except Exception as e:
        context = {
            'error_message': str(e),
            'current_datetime': datetime.datetime.now(),
        }
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
        messages.success(request, 'Chief complains have been updated successfully.')

        # Generate the URL with the query parameter
        redirect_url = reverse('drloa') + f'?appointment_id={appointment_id}'
        return HttpResponseRedirect(redirect_url)

    except Exception as e:
        print(f"Error saving chief complains: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('doctor_dashboard')
    

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
        print(f'Treatment plans saved for appointment ID: {appointment_id}')
        messages.success(request, 'Treatment plans have been updated successfully.')

        # Generate the URL with the query parameter
        redirect_url = reverse('drloa') + f'?appointment_id={appointment_id}'
        return HttpResponseRedirect(redirect_url)

    except Exception as e:
        print(f"Error saving treatment plans: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('doctor_dashboard')
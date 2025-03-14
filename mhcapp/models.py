# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.contrib.auth.models import BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, phone, name, role, password=None, **extra_fields):
        if not phone:
            raise ValueError('Users must have a phone number')
        user = self.model(
            phone=phone,
            name=name,
            role=role,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone, name, role, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone, name, role, password, **extra_fields)

class RoleCounter(models.Model):
    role = models.CharField(max_length=10, unique=True)
    count = models.PositiveIntegerField(default=0)

class User(AbstractUser):
    objects = UserManager()

    ROLES = (
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('labt', 'Lab Technician'),
        ('rg', 'Radiographer'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLES)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, unique=True)
    custom_id = models.CharField(max_length=20, unique=True, blank=True)

    username = None
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['name', 'role']

    def save(self, *args, **kwargs):
        if not self.custom_id:
            # Ensure role is set and normalized to lowercase before generating ID
            print(f'role in the save method user class in models.py: {self.role}')
            if not self.role:
                self.role = 'patient'  # Default role
            else:
                self.role = self.role.lower()
                print(f'role in the save method user class in models.py: {self.role}')
                
            role_prefixes = {
                'patient': 'PAT',
                'doctor': 'DOC',
                'nurse': 'NUR',
                'labt': 'LAB',
                'rg': 'RAD',
                'admin': 'ADM'
            }
            prefix = role_prefixes.get(self.role, 'USR')
            
            from django.db import transaction
            with transaction.atomic():
                counter, created = RoleCounter.objects.select_for_update().get_or_create(role=self.role)
                counter.count += 1
                counter.save()
                self.custom_id = f"{prefix}{counter.count:03d}"
        super().save(*args, **kwargs)


# models.py
class Patient(models.Model):
    GENDER_CHOICES = (('M', 'Male'), ('F', 'Female'), ('O', 'Other'))
    user = models.OneToOneField(
        'User',  # Use string reference
        on_delete=models.CASCADE,
        primary_key=True
    )    
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    address = models.TextField()

    # # Additional fields for patient details
    # height = models.IntegerField(null=True, blank=True)  # Height in cm
    # weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # Weight in kg
    # allergies = models.TextField(blank=True, null=True)
    # blood_type = models.CharField(max_length=5, blank=True, null=True)

class Doctor(models.Model):
    user = models.OneToOneField(
        'User',  # Use string reference
        on_delete=models.CASCADE, 
        primary_key=True
    )
    speciality = models.CharField(max_length=100)

# models proxies
class AdminProxy(User):
    class Meta:
        proxy = True
        verbose_name = 'Admin'
        verbose_name_plural = 'Admins'
    
    def save(self, *args, **kwargs):
        # Force role to be 'admin' before saving
        if not self.role or self.role.lower() != 'admin':
            self.role = 'admin'
        super().save(*args, **kwargs)
    role='admin'

class PatientProxy(User):
    class Meta:
        proxy = True
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'
    def save(self, *args, **kwargs):
        # Force role to be 'patient' before saving
        if not self.role or self.role.lower() != 'patient':
            self.role = 'patient'
        super().save(*args, **kwargs)
    role = 'patient'  

class DoctorProxy(User):
    class Meta:
        proxy = True
        verbose_name = 'Doctor'
        verbose_name_plural = 'Doctors'
    def save(self, *args, **kwargs):
        # Force role to be 'doctor' before saving
        if not self.role or self.role.lower() != 'doctor':
            self.role = 'doctor'
        super().save(*args, **kwargs)
    role = 'doctor'

class NurseProxy(User):
    class Meta:
        proxy = True
        verbose_name = 'Nurse'
        verbose_name_plural = 'Nurses'
    def save(self, *args, **kwargs):
        # Force role to be 'nurse' before saving
        if not self.role or self.role.lower() != 'nurse':
            self.role = 'nurse'
        super().save(*args, **kwargs)
    role = 'nurse'

class LabTechProxy(User):
    class Meta:
        proxy = True
        verbose_name = 'Lab Technician'
        verbose_name_plural = 'Lab Technicians'
    def save(self, *args, **kwargs):
        # Force role to be 'labt' before saving
        if not self.role or self.role.lower() != 'labt':
            self.role = 'labt'
        super().save(*args, **kwargs)
    role = 'labt'

class RadiographerProxy(User):
    class Meta:
        proxy = True
        verbose_name = 'Radiographer'
        verbose_name_plural = 'Radiographers'
    def save(self, *args, **kwargs):
        # Force role to be 'rg' before saving
        if not self.role or self.role.lower() != 'rg':
            self.role = 'rg'
        super().save(*args, **kwargs)
    role = 'rg'

# Appointment models
class Appointment(models.Model):
    appointment_id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    appointment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='pending')

    def __str__(self):
        return f"Appointment {self.appointment_id} - {self.patient.user.name} with {self.doctor.user.name}"

# Vitals models
class VitalsRecord(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='vitals_records')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Vitals measurements
    systolic_bp = models.IntegerField(null=True, blank=True)
    diastolic_bp = models.IntegerField(null=True, blank=True)
    pulse_rate = models.IntegerField(null=True, blank=True)
    spo2 = models.IntegerField(null=True, blank=True)
    respiratory_rate = models.IntegerField(null=True, blank=True)
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    
    # BMI can be calculated on the fly, but we'll store it for historical records
    bmi = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    
    # Other information
    allergies = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    # Record who entered this data
    entered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='entered_vitals')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Vitals for {self.appointment.patient.user.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def calculate_bmi(self):
        if self.weight and self.height and self.height > 0:
            # Height is in cm, weight in kg
            height_in_meters = self.height / 100
            return round(self.weight / (height_in_meters ** 2), 1)
        return None
    
    def save(self, *args, **kwargs):
        # Calculate BMI before saving if possible
        if not self.bmi:
            self.bmi = self.calculate_bmi()
        super().save(*args, **kwargs)


#  Lab Test models
class LabTest(models.Model):
    name = models.CharField(max_length=200, unique=True)
    
    def __str__(self):
        return self.name

class Subtest(models.Model):
    test = models.ForeignKey(LabTest, on_delete=models.CASCADE, related_name='subtests')
    name = models.CharField(max_length=200)
    male_normal_low = models.FloatField(null=True, blank=True)
    male_normal_high = models.FloatField(null=True, blank=True)
    female_normal_low = models.FloatField(null=True, blank=True)
    female_normal_high = models.FloatField(null=True, blank=True)
    unit = models.CharField(max_length=50)
    
    def __str__(self):
        return f"{self.test.name} - {self.name}"
    
# Ongoing Medication models
class Medication(models.Model):
    """Model to store medication information for appointments"""
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='medications')
    description = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        
    def __str__(self):
        return f"{self.description} - {self.appointment}"
    
# Previous Diagnosis models
class PreviousDiagnosis(models.Model):
    """Model to store previous diagnosis information for appointments"""
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='previous_diagnoses')
    description = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        
    def __str__(self):
        return f"{self.description} - {self.appointment}"
    
# Chief Complaint models
class ChiefComplain(models.Model):
    """Model to store chief complain information for appointments"""
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='chief_complains')
    description = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        
    def __str__(self):
        return f"{self.description} - {self.appointment}"
    

# Current diagnosis models
class CurrentDiagnosis(models.Model):
    """Model to store current diagnosis information for appointments"""
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='current_diagnoses')
    description = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        
    def __str__(self):
        return f"{self.description} - {self.appointment}"
    
# Treatment plan models:
class TreatmentPlan(models.Model):
    """Model to store treatment plan information for appointments"""
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='treatment_plans')
    description = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        
    def __str__(self):
        return f"{self.description} - {self.appointment}"
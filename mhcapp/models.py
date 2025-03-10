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


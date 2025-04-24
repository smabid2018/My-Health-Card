from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.login_view, name="login"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    #path("", views.home, name="home"),
    path('doctor-dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('drloa/', views.drloa, name='drloa'),
    path("loa/", views.loa, name="loa"),  # ← Changed name to "loa"
    path("ongoingMedication/", views.ongoingMedication, name="ongoingMedication"),
    path("previousDiagnosis/", views.previousDiagnosis, name="previousDiagnosis"),
    path("chiefComplain/", views.chiefComplain, name="chiefComplain"),
    path("currentDiagnosis/", views.currentDiagnosis, name="currentDiagnosis"),
    path('treatmentPlan/', views.treatmentPlan, name='treatmentPlan'),
    path('physicalExam/', views.physicalExam, name='physicalExam'),

    path('request_investigation/', views.request_investigation, name='request_investigation'),
    path('cancel_investigation/<int:investigation_id>/', views.cancel_investigation, name='cancel_investigation'),
    path('view_investigation/<int:investigation_id>/', views.view_investigation, name='view_investigation'),
    path('predict_diagnosis/<int:investigation_id>/', views.predict_diagnosis, name='predict_diagnosis'),

    path("admin_dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("newappointment/", views.newappointment, name="newappointment"),
    
    path("nursedash/", views.nursedash, name="nursedash"),
    path("vitalsentry/", views.vitalsentry, name="vitalsentry"),
    
    path("radiographerdash/", views.radiographerdash, name="radiographerdash"),
    path('radnewreq/<int:investigation_id>/', views.radnewreq, name='radnewreq'),
    path('upload_report/<int:investigation_id>/', views.upload_report, name='upload_report'),


    path("techdash/", views.techdash, name="techdash"),
    path('techreqdetails/<int:investigation_id>/', views.techreqdetails, name='techreqdetails'),

    

    path("patient_dashboard/", views.patient_dashboard, name="patient_dashboard"),
    path('view-appointment/<int:appointment_id>/', views.view_patient_appointment, name='view_patient_appointment'),
    path('view_my_investigation/<int:investigation_id>/', views.view_my_investigation, name='view_my_investigation'),
    
    
    
]


# ⭐ To serve media files in development ⭐
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('patient/', views.patient_dashboard, name='patient_dashboard'),
    path('clinician/', views.clinician_dashboard, name='clinician_dashboard'),
    path('view-patient/', views.view_patient, name='view_patient'),  # 👈 ADD THIS
    path('rom-test/', views.rom_test_intro, name='rom_test_intro'),
    path('rom-test/run/<str:rom_type>/', views.rom_test_measure, name='rom_test_measure'),
    path('save-rom-test/', views.save_rom_test, name='save_rom_test'),
    path('rom-history/trend/', views.rom_history_trend, name='rom_history_trend'),
    path('rom-history/log/', views.rom_history_log, name='rom_history_log'),
    path('rehab/', views.rehab_program, name='rehab_program'),
    path('rehab/mark/<int:exercise_id>/', views.mark_exercise_complete, name='mark_exercise_complete'),
    path('clinician/resolve_warning/<int:warning_id>/', views.resolve_warning, name='resolve_warning'),
    path('chatbot/ask/', views.chatbot_ask, name='chatbot_ask'),
    path('export/pdf/', views.export_rom_pdf, name='export_rom_pdf'),


]

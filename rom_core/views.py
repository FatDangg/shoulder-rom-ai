from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, UserLoginForm
from .models import UserProfile
import random
import string
from .models import ROMWarning
from .models import Exercise, RehabSchedule, ExerciseCompletion, RehabSessionFeedback


# Home Page View
def home(request):
    if request.user.is_authenticated:
        try:
            role = request.user.userprofile.role
            if role == 'patient':
                return redirect('patient_dashboard')
            elif role == 'clinician':
                return redirect('clinician_dashboard')
        except UserProfile.DoesNotExist:
            pass  # fallback to default homepage if no role found
    return render(request, 'home.html')


# Generate unique code for patients
def generate_code(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# Registration View
def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            role = form.cleaned_data['role']
            code = generate_code() if role == 'patient' else None
            UserProfile.objects.create(user=user, role=role, unique_code=code)
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})

# Login View
def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            if user:
                login(request, user)
                role = user.userprofile.role
                if role == 'patient':
                    return redirect('patient_dashboard')
                elif role == 'clinician':
                    return redirect('clinician_dashboard')
            else:
                return render(request, 'login.html', {'form': form, 'error': 'Invalid credentials'})
    else:
        form = UserLoginForm()
    return render(request, 'login.html', {'form': form})

# Logout View
def logout_view(request):
    logout(request)
    return redirect('login')

from .models import ROMTest

@login_required
def patient_dashboard(request):
    import json

    active_warnings = ROMWarning.objects.filter(user=request.user, resolved=False).order_by('-created_at')
    rom_tests = list(ROMTest.objects.filter(user=request.user).order_by('-timestamp'))
    rom_tests.reverse()  # oldest first for graphs and summary

    # Arrays for legacy table display (optional)
    rom_dates = [test.timestamp.strftime('%Y-%m-%d %H:%M') for test in rom_tests]
    rom_flexion = [test.flexion for test in rom_tests]
    rom_extension = [test.extension for test in rom_tests]
    rom_abduction = [test.abduction for test in rom_tests]
    rom_adduction = [test.adduction for test in rom_tests]

    # Arrays for Chart.js time series (RECOMMENDED)
    rom_flexion_data = [{"x": test.timestamp.isoformat(), "y": test.flexion} for test in rom_tests]
    rom_extension_data = [{"x": test.timestamp.isoformat(), "y": test.extension} for test in rom_tests]
    rom_abduction_data = [{"x": test.timestamp.isoformat(), "y": test.abduction} for test in rom_tests]
    rom_adduction_data = [{"x": test.timestamp.isoformat(), "y": test.adduction} for test in rom_tests]

    # For summary arrows
    if len(rom_tests) >= 2:
        latest = rom_tests[-1]
        previous = rom_tests[-2]
    else:
        latest = rom_tests[-1] if rom_tests else None
        previous = None

    rom_summary = {}
    for rom_type in ['flexion', 'extension', 'abduction', 'adduction']:
        if latest and previous:
            diff = getattr(latest, rom_type) - getattr(previous, rom_type)
            trend = "up" if diff > 0 else "down" if diff < 0 else "equal"
        else:
            trend = "equal"
        rom_summary[rom_type] = {
            'value': getattr(latest, rom_type) if latest else None,
            'trend': trend
        }

    # Merge everything into one context dict!
    context = {
        'active_warnings': active_warnings,
        'rom_tests': rom_tests,
        'rom_dates': rom_dates,
        'rom_flexion': rom_flexion,
        'rom_extension': rom_extension,
        'rom_abduction': rom_abduction,
        'rom_adduction': rom_adduction,
        'rom_summary': rom_summary,
        # For Chart.js:
        'rom_flexion_data': json.dumps(rom_flexion_data),
        'rom_extension_data': json.dumps(rom_extension_data),
        'rom_abduction_data': json.dumps(rom_abduction_data),
        'rom_adduction_data': json.dumps(rom_adduction_data),
    }

    return render(request, 'patient_dashboard.html', context)



from django.contrib.auth.decorators import login_required
from .models import ROMWarning

@login_required
def clinician_dashboard(request):
    # Get all unresolved warnings for all patients, newest first
    rom_tests = ROMTest.objects.filter(user=request.user).order_by('-timestamp')
    rom_tests.reverse()
    return render(request, 'clinician_dashboard.html', {
        'active_warnings': active_warnings,
    })

from django.contrib.auth.models import User
from django.http import HttpResponse

@login_required
def view_patient(request):
    code = request.GET.get('code')
    try:
        patient_profile = UserProfile.objects.get(unique_code=code, role='patient')
        return render(request, 'view_patient.html', {'patient': patient_profile})
    except UserProfile.DoesNotExist:
        return HttpResponse("Patient not found.", status=404)

@login_required
def rom_test_intro(request):
    return render(request, 'rom_test_intro.html')

@login_required
def rom_test_measure(request, rom_type):
    return render(request, 'rom_test_measure.html', {'rom_type': rom_type.upper()})


from django.http import JsonResponse
from .models import ROMTest
from django.contrib.auth.decorators import login_required
import json
from .utils import check_frozen_shoulder_risk
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@login_required
def save_rom_test(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        ROMTest.objects.create(
            user=request.user,
            flexion=data['flexion'],
            extension=data['extension'],
            abduction=data['abduction'],
            adduction=data['adduction']
        )
        check_frozen_shoulder_risk(request.user)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)


from .models import ROMTest

@login_required
def rom_history_trend(request):
    rom_tests = ROMTest.objects.filter(user=request.user).order_by('timestamp')
    return render(request, 'partials/rom_history_trend.html', {'rom_tests': rom_tests})

@login_required
def rom_history_log(request):
    rom_tests = ROMTest.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'partials/rom_history_log.html', {'rom_tests': rom_tests})

from datetime import date
from .models import Exercise, ExerciseCompletion

@login_required
def rehab_program(request):
    exercises = Exercise.objects.all()
    today = date.today()
    completed = ExerciseCompletion.objects.filter(user=request.user, date=today).values_list('exercise_id', flat=True)

    return render(request, 'rehab_program.html', {
        'exercises': exercises,
        'completed': list(completed),
        'today': today
    })

from django.shortcuts import redirect, get_object_or_404

@login_required
def mark_exercise_complete(request, exercise_id):
    today = date.today()
    exercise = get_object_or_404(Exercise, id=exercise_id)
    ExerciseCompletion.objects.get_or_create(user=request.user, exercise=exercise, date=today)
    return redirect('rehab_program')


from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Exercise, RehabSchedule, ExerciseCompletion

@login_required
def rehab_program(request):
    today = date.today()
    try:
        schedule = RehabSchedule.objects.get(user=request.user, date=today)
        exercises = schedule.exercises.all()
    except RehabSchedule.DoesNotExist:
        exercises = Exercise.objects.all()

    completed = ExerciseCompletion.objects.filter(user=request.user, date=today).values_list('exercise_id', flat=True)
    completed_set = set(completed)
    num_completed = len(completed_set)
    total_today = exercises.count()

    # Progress percent for the bar
    if total_today:
        percent_complete = int(num_completed / total_today * 100)
    else:
        percent_complete = 0

    # Weekly calendar (streak only if all assigned exercises are completed)
    week_dates = [today - timedelta(days=i) for i in range(6, -1, -1)]
    week_completions = []
    for d in week_dates:
        try:
            sched = RehabSchedule.objects.get(user=request.user, date=d)
            exs = sched.exercises.all()
            total = exs.count()
        except RehabSchedule.DoesNotExist:
            exs = Exercise.objects.all()
            total = exs.count()
        done = ExerciseCompletion.objects.filter(user=request.user, date=d).values_list('exercise_id', flat=True)
        week_completions.append({'date': d, 'completed': (total > 0 and len(set(done)) == total)})

    streak = 0
    for info in reversed(week_completions):
        if info['completed']:
            streak += 1
        else:
            break

    # Done for today?
    all_done = (total_today > 0 and num_completed == total_today)

    # Feedback
    # Check if feedback already exists for today
    feedback_obj = RehabSessionFeedback.objects.filter(user=request.user, date=today).first()
    feedback_submitted = feedback_obj is not None

    # Handle feedback submission
    if all_done and request.method == "POST" and not feedback_submitted and 'pain_level' in request.POST:
        pain_level = int(request.POST.get('pain_level', 0))
        feedback = request.POST.get('feedback', '')
        RehabSessionFeedback.objects.create(
            user=request.user, date=today,
            pain_level=pain_level, feedback=feedback
        )
        feedback_submitted = True



    return render(request, 'rehab_program.html', {
        'exercises': exercises,
        'completed': list(completed),
        'today': today,
        'week_completions': week_completions,
        'streak': streak,
        'num_completed': num_completed,
        'total_today': total_today,
        'all_done': all_done,
        'feedback_submitted': feedback_submitted,
        'percent_complete': percent_complete,  # <-- pass this to template
    })


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

@login_required
def resolve_warning(request, warning_id):
    if request.method == 'POST':
        warning = get_object_or_404(ROMWarning, pk=warning_id)
        warning.resolved = True
        warning.save()
        messages.success(request, f'Warning {warning.warning_type} resolved.')
    return redirect('clinician_dashboard')


import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

# Google Gemini import (assuming you have google-generativeai installed)
import google.generativeai as genai

genai.configure(api_key="AIzaSyDxtCuqZMliYZNPNAuw2Lfm3y8FnV270QA")

@csrf_exempt   # For demo/dev only. For production, use proper CSRF protection!
@login_required
def chatbot_ask(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get('message', '')
        # Safety: Check message length/content here if needed

        # Gemini interaction
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(user_message)
        reply = response.text if hasattr(response, 'text') else str(response)

        return JsonResponse({'reply': reply})
    return JsonResponse({'reply': 'Error: Only POST allowed.'}, status=400)



import base64
from io import BytesIO
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from .models import ROMTest

import base64
from io import BytesIO
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from PIL import Image as PilImage
from .models import ROMTest

@login_required
def export_rom_pdf(request):
    if request.method != "POST":
        return HttpResponse("Invalid request", status=400)
    
    # 1. Get chart image from form POST (the hidden input)
    chart_image_b64 = request.POST.get("chart_image_field")
    if not chart_image_b64:
        return HttpResponse("No image data", status=400)
    
    try:
        header, img_data = chart_image_b64.split(',', 1)
        chart_image_bytes = base64.b64decode(img_data)
        chart_image_io = BytesIO(chart_image_bytes)
        # Ensure image is RGB to avoid black/white inversion
        img = PilImage.open(chart_image_io).convert('RGB')
        rgb_buffer = BytesIO()
        img.save(rgb_buffer, format='JPEG')
        rgb_buffer.seek(0)
    except Exception as e:
        return HttpResponse(f"Error decoding or processing image: {e}", status=400)

    # 2. Create PDF document
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title and user info
    story.append(Paragraph("Shoulder ROM Report", styles['Title']))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Patient: {request.user.username}", styles['Normal']))
    story.append(Spacer(1, 10))

    # 3. Add chart image, scaled to fit
    img_width = 400  # points (about 5.5in)
    img_height = int(img.size[1] * (img_width / img.size[0]))
    story.append(Image(rgb_buffer, width=img_width, height=img_height))
    story.append(Spacer(1, 16))

    # 4. Add ROM history table
    rom_tests = ROMTest.objects.filter(user=request.user).order_by('timestamp')
    table_data = [["Date", "Flexion", "Extension", "Abduction", "Adduction"]]
    for test in rom_tests:
        table_data.append([
            test.timestamp.strftime("%Y-%m-%d"),
            f"{test.flexion:.1f}",
            f"{test.extension:.1f}",
            f"{test.abduction:.1f}",
            f"{test.adduction:.1f}",
        ])
    table = Table(table_data, hAlign='LEFT')
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightblue),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("ALIGN", (1,1), (-1,-1), "CENTER"),
    ]))
    story.append(table)
    story.append(Spacer(1, 24))

    # 5. Optional: Closing message
    story.append(Paragraph("Thank you for using the Shoulder ROM Tracker!", styles['Italic']))

    # 6. Build and return the PDF
    doc.build(story)
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type='application/pdf')

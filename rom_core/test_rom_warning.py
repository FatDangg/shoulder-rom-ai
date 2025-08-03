import sys
import os

# Ensure the project root (the parent of 'rom_backend') is in the path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rom_backend.settings')
import django
django.setup()

from django.contrib.auth.models import User
from rom_core.models import ROMTest, ROMWarning
from rom_core.utils import check_frozen_shoulder_risk  # Or from rom_core.views if you put it there
from datetime import datetime, timedelta

# Get a test user
u = User.objects.first()

# Create 3 ROMTest entries on different days with low adduction to simulate risk
for i in range(3):
    ROMTest.objects.create(
        user=u,
        timestamp=datetime.now() - timedelta(days=2-i),
        flexion=150,        # normal value
        extension=55,       # normal value
        abduction=160,      # normal value
        adduction=15        # *LOW* value for risk detection
    )

# Run your risk detection (adjust for the rule you want to check)
check_frozen_shoulder_risk(u)

# Show warnings
warnings = ROMWarning.objects.filter(user=u).order_by('-created_at')
for w in warnings:
    print(w.warning_type, w.details, w.created_at)


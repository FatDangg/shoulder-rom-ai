from .models import ROMTest, ROMWarning
from datetime import date

def check_frozen_shoulder_risk(user):
    """
    Checks the last 3 ROMTest entries for various clinical risk patterns.
    Adds a ROMWarning if a pattern is detected and not already present today.
    """

    recent_tests = ROMTest.objects.filter(user=user).order_by('-timestamp')[:3]

    if len(recent_tests) < 3:
        return  # Not enough data to check trends

    # Gather values for each type
    flexion_vals    = [test.flexion for test in recent_tests if test.flexion is not None]
    extension_vals  = [test.extension for test in recent_tests if test.extension is not None]
    abduction_vals  = [test.abduction for test in recent_tests if test.abduction is not None]
    adduction_vals  = [test.adduction for test in recent_tests if test.adduction is not None]

    # Example rules (edit thresholds as needed for your clinic!)
    today = recent_tests[0].timestamp.date()

    # Flexion < 90° three times in a row
    if len(flexion_vals) == 3 and all(v < 90 for v in flexion_vals):
        ROMWarning.objects.get_or_create(
            user=user,
            date=today,
            warning_type="Flexion Low",
            defaults={'details': f"Last 3: {flexion_vals}"}
        )

    # Extension < 30° three times in a row
    if len(extension_vals) == 3 and all(v < 30 for v in extension_vals):
        ROMWarning.objects.get_or_create(
            user=user,
            date=today,
            warning_type="Extension Low",
            defaults={'details': f"Last 3: {extension_vals}"}
        )

    # Abduction < 90° three times in a row
    if len(abduction_vals) == 3 and all(v < 90 for v in abduction_vals):
        ROMWarning.objects.get_or_create(
            user=user,
            date=today,
            warning_type="Abduction Low",
            defaults={'details': f"Last 3: {abduction_vals}"}
        )

    # Adduction < 10° three times in a row (threshold is low because normal is up to 30)
    if len(adduction_vals) == 3 and all(v < 10 for v in adduction_vals):
        ROMWarning.objects.get_or_create(
            user=user,
            date=today,
            warning_type="Adduction Low",
            defaults={'details': f"Last 3: {adduction_vals}"}
        )

    # Example: >50% drop in abduction vs. previous average (skip if not enough data)
    if len(recent_tests) == 3:
        this_abd = recent_tests[0].abduction
        prev_abd_avg = (recent_tests[1].abduction + recent_tests[2].abduction) / 2
        if prev_abd_avg > 0 and this_abd < 0.5 * prev_abd_avg:
            ROMWarning.objects.get_or_create(
                user=user,
                date=today,
                warning_type="Abduction Dropped >50%",
                defaults={'details': f"Today: {this_abd:.1f}, Prev avg: {prev_abd_avg:.1f}"}
            )

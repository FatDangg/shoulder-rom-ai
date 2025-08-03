from django.contrib import admin
from .models import UserProfile
from .models import ROMTest

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'unique_code')
    search_fields = ('user__username', 'user__email', 'unique_code')
    list_filter = ('role',)

@admin.register(ROMTest)
class ROMTestAdmin(admin.ModelAdmin):
    list_display = ('user', 'timestamp', 'flexion', 'extension', 'abduction', 'adduction')
    list_filter = ('user', 'timestamp')
    search_fields = ('user__username',)

admin.site.register(UserProfile, UserProfileAdmin)

from .models import Exercise, ExerciseCompletion, RehabSchedule
admin.site.register(Exercise)
admin.site.register(ExerciseCompletion)
admin.site.register(RehabSchedule)

from .models import RehabSessionFeedback
admin.site.register(RehabSessionFeedback)

from django.contrib import admin
from .models import ROMTest, ROMWarning, RehabSessionFeedback, Exercise, RehabSchedule, ExerciseCompletion

@admin.register(ROMWarning)
class ROMWarningAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "warning_type", "resolved", "created_at")
    list_filter = ("resolved", "warning_type", "date")
    search_fields = ("user__username", "warning_type", "details")
    readonly_fields = ("created_at",)
    actions = ["mark_as_resolved", "mark_as_unresolved"]

    def mark_as_resolved(self, request, queryset):
        queryset.update(resolved=True)
    mark_as_resolved.short_description = "Mark selected warnings as resolved"

    def mark_as_unresolved(self, request, queryset):
        queryset.update(resolved=False)
    mark_as_unresolved.short_description = "Mark selected warnings as unresolved"


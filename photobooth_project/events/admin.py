from django.contrib import admin
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'guest_code', 'created_at', 'is_active')
    readonly_fields = ('id', 'guest_code', 'owner_secret', 'created_at')

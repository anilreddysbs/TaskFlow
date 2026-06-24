from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'actor', 'message', 'read', 'created_at')
    list_filter = ('read', 'created_at', 'recipient', 'actor')
    search_fields = ('message', 'recipient__username', 'actor__username')
    readonly_fields = ('created_at',)


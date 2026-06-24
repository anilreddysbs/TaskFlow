from django.contrib import admin
from .models import Project

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'team', 'created_by', 'created_at')
    list_filter = ('team', 'created_by', 'created_at')
    search_fields = ('name', 'team__name', 'created_by__username')
    readonly_fields = ('created_at', 'updated_at')
from django.contrib import admin
from .models import Comment

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'task', 'created_at')
    list_filter = ('author', 'task', 'created_at')
    search_fields = ('content', 'author__username', 'task__title')
    readonly_fields = ('created_at', 'updated_at')
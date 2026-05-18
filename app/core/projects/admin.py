from django.contrib import admin

from core.projects.models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_visible', 'active', 'updated_at')
    list_filter = ('is_visible', 'active')
    search_fields = ('name',)
    ordering = ('-updated_at', '-id')
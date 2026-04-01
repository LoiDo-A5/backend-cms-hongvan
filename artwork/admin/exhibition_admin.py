from django.contrib import admin


class ExhibitionAdmin(admin.ModelAdmin):
    list_display = ('title', 'date_start', 'date_end', 'organizer_name', 'event_type')
    search_fields = ('title', 'organizer_name', 'address', 'preface')
    list_filter = ('event_type', 'date_start', 'date_end')

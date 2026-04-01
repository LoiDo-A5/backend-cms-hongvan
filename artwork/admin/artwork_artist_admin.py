from django.contrib import admin


class ArtworkArtistAdmin(admin.ModelAdmin):
    list_display = ('id', 'artist_name', 'contact_info', 'year_of_birth')

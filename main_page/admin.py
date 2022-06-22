from django.contrib import admin
from . import models
# Register your models here.

class AlbumModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'artists', 'name', 'spotify_id')
    search_fields = ('id', 'name', 'spotify_id')


class ArtistModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'spotify_id')
    search_fields = ('id', 'name', 'spotify_id')


class SongModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'artists', 'album', 'name', 'track_number', 'spotify_id')
    list_display_links = ('id', 'name')
    search_fields = ('id', 'name', 'spotify_id')


class UpcomingAlbumEntryModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'artists', 'album_name', 'release_date', 'album')
    list_display_links = ('id', 'album_name')
    search_fields = ('id', 'album_name')


admin.site.register(models.UpcomingAlbumEntryModel, UpcomingAlbumEntryModelAdmin)
admin.site.register(models.ArtistModel, ArtistModelAdmin)
admin.site.register(models.AlbumModel, AlbumModelAdmin)
admin.site.register(models.SongModel, SongModelAdmin)

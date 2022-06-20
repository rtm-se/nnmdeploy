from django.contrib import admin
from . import models
# Register your models here.


class SpotifyTokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'user', 'expires_in', 'token_type')
    list_display_links = ('id', 'user')
    search_fields = ('id', 'user__username')


class SpotifyProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'display_name', 'spotify_id')
    list_display_links = ('id', 'user')
    search_fields = ('id', 'user__username')


admin.site.register(models.SpotifyToken, SpotifyTokenAdmin)
admin.site.register(models.SpotifyProfile, SpotifyProfileAdmin)
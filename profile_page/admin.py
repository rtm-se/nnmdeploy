from django.contrib import admin
from . import models
# Register your models here.


class EncounteredAlbumModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'album', 'completion', 'visible')
    search_fields = ('id', 'user__username', 'album__name')
    list_editable = ('visible',)


class ProfileModelAdmin(admin.ModelAdmin):
    list_display = ('user', 'reviews_visibility', 'likes_visibility', 'encountered_visibility')
    search_fields = ('user__username',)
    list_editable = ('reviews_visibility', 'likes_visibility', 'encountered_visibility')


class ReviewModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'album', 'created')
    search_fields = ('id', 'user__username', 'album__name')


class LikeModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'album', 'visible')
    search_fields = ('id', 'user__username', 'album__name')
    list_editable = ('visible',)


class ListenedSongsModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'song', 'played_at')
    search_fields = ('id', 'user__username', 'song__name')


class WaitingListAlbumModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'upcoming_album')
    search_fields = ('id', 'user__username', 'upcoming_album__album_name')


class RecommendationModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'album')
    search_fields = ('id', 'user__username', 'album__name')


class SpotifyLikeModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'song')
    search_fields = ('id', 'user__username', 'song__name', 'song__album__name')


class SpotifySavedAlbumModerlAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'album')
    search_fields = ('id', 'user__username', 'album__name')


class SpotifyFollowedArtistModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'artist')
    search_fields = ('id', 'user__username', 'artist__name')


admin.site.register(models.ProfileModel, ProfileModelAdmin)
admin.site.register(models.ReviewModel, ReviewModelAdmin)
admin.site.register(models.LikeModel, LikeModelAdmin)
admin.site.register(models.ListenedSongsModel, ListenedSongsModelAdmin)
admin.site.register(models.EncounteredAlbumModel, EncounteredAlbumModelAdmin)
admin.site.register(models.WaitingListAlbumModel, WaitingListAlbumModelAdmin)
admin.site.register(models.RecommendationModel, RecommendationModelAdmin)
admin.site.register(models.SpotifyLikeModel, SpotifyLikeModelAdmin)
admin.site.register(models.SpotifySavedAlbumModerl, SpotifySavedAlbumModerlAdmin)
admin.site.register(models.SpotifyFollowedArtistModel, SpotifyFollowedArtistModelAdmin)

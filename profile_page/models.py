from django.db import models
from django.contrib.auth.models import User
from main_page.models import AlbumModel, SongModel, UpcomingAlbumEntryModel, ArtistModel
# Create your models here.
from django.utils.timezone import now
from django.db.models.signals import post_save

class ProfileModel(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='profile'
    )
    pfp = models.ImageField(default='default_pfp.png')
    bio = models.TextField(blank=True, null=True, max_length=400)
    reviews_visibility = models.BooleanField(default=True)
    likes_visibility = models.BooleanField(default=True)
    encountered_visibility = models.BooleanField(default=True)
    favorite_album = models.ForeignKey(AlbumModel, on_delete=models.SET_NULL, null=True, blank=True, related_name='fav_album')
    playlist_albums = models.ManyToManyField(
        AlbumModel,
        blank=True,

    )
    #liked_album = models.ManyToManyField(AlbumModel, related_name='album_like')



class ReviewModel(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        related_query_name='review'
    )
    album = models.ForeignKey(
        AlbumModel,
        on_delete=models.RESTRICT,
        related_name='reviews',
        related_query_name='review'
    )
    recommended = models.BooleanField(null=True)
    #todo get median review length
    body = models.TextField(max_length=400)
    created = models.DateTimeField(auto_now_add=True)


class LikeModel(models.Model):
    visible = models.BooleanField()
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='likes',
        related_query_name='like'

    )
    album = models.ForeignKey(
        AlbumModel,
        on_delete=models.CASCADE,
        related_name='likes',
        related_query_name='like'
    )


    def is_liked(self, user_model):
        if LikeModel.objects.filter(user=user_model, album=self.album).exists():
            return True
        else:
            return False


class ListenedSongsModel(models.Model):
    played_at = models.CharField(max_length=100, default='bruh')
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='songs',
        related_query_name='song'
    )

    song = models.ForeignKey (
        SongModel,
        on_delete=models.CASCADE,
        related_name='users',
        related_query_name='user'
    )
    class Meta:
        ordering = ['played_at']


class EncounteredAlbumModel(models.Model):
    visible = models.BooleanField(default=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='encountered_albums',
        related_query_name='encountered_album'
    )

    album = models.ForeignKey(
        AlbumModel,
        on_delete=models.CASCADE,
        related_name='encountered_users',
        related_query_name='encountered_user'
    )

    completion = models.SmallIntegerField(default=0)
    songs_count = models.SmallIntegerField(default=0)

    def get_song_completion(self):
        #check if comletion is 100% then skip
        if self.completion != 100:
            # get songs unique songs listened on the album
            new_songs_count = len(set(ListenedSongsModel.objects.filter(
                user=self.user,
                song__album=self.album).values_list('song__name')))
            #checking if the number of songs listened on the album changed
            if new_songs_count != self.songs_count:
                self.songs_count = new_songs_count
                # getting % of album listened
                completion_percentage = (100 / self.album.total_tracks) * new_songs_count
                #updating model
                self.completion = int(completion_percentage)
                self.save()

        #return int(completion_percentage)


    class Meta:
        ordering = ['completion']


class WaitingListAlbumModel(models.Model):
    visible = models.BooleanField(default=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='waiting_list',
        related_query_name='waiting_list'
    )

    upcoming_album = models.ForeignKey(
        UpcomingAlbumEntryModel,
        on_delete=models.CASCADE,
        related_name='upcoming_users',
        related_query_name='upcoming_user'
    )

    class Meta:
        ordering = ['upcoming_album']


class RecommendationModel(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recommendation_albums',
        related_query_name='recommendation_album'
    )

    album = models.ForeignKey(
        AlbumModel,
        on_delete=models.CASCADE,
        related_name='recommendation_users',
        related_query_name='recommendation_user'
    )

    class Meta:
        ordering = ['album']



class SpotifyLikeModel(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='SpotifyLike'
    )
    song = models.ForeignKey(
        SongModel,
        on_delete=models.CASCADE,
        related_name='SpotifyUserLiked'
    )


class SpotifySavedAlbumModerl(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='SpotifySavedAlbum'
    )
    album = models.ForeignKey(
        AlbumModel,
        on_delete=models.CASCADE,
        related_name='SpotifyUserSaved'
    )


class SpotifyFollowedArtistModel(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='SpotifyFollowedArtist'
    )
    artist = models.ForeignKey(
        ArtistModel,
        on_delete=models.CASCADE,
        related_name='SpotifyFollowedArtist'
    )
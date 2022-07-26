import datetime
from django.db import models
# Create your models here.


class ArtistModel(models.Model):
    name = models.CharField(max_length=200, unique=False)
    artist_link = models.CharField(max_length=200)
    genres = models.CharField(max_length=300, blank=True, null=True)
    spotify_id = models.CharField(max_length=50, blank=True)

    def give_uri(self):
        return self.artist_link.split('/')[-1]

    def __str__(self):
        return self.name


class UpcomingAlbumEntryModel(models.Model):
    artist_name = models.ManyToManyField(
        ArtistModel,
        related_name='upcoming_albums',
        related_query_name='Upcoming_album',
    )
    #artist_name = models.CharField(max_length=50)
    album_name = models.CharField(max_length=50, unique=False)
    release_date = models.DateField()
    description = models.TextField(max_length=200, blank=True, null=True)
    cover = models.ImageField(null=True, default='cover.jfif')
    cover_link = models.URLField(
        blank=True,
        default='https://uevicgzbyqusuokdtbwi.supabase.co/storage/v1/object/public/nnm-bucket/img_11809-1141319174.png',
        max_length=400
    )
    album = models.ForeignKey(
        'AlbumModel',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def artists(self):
        artists_name = self.artist_name.all()
        artists_string = []
        for artist in artists_name:
            artists_string.append(artist.name)
        return ", ".join(artists_string)

    class Meta:
        ordering = ["release_date"]

    def  __str__(self):
        return f'{self.album_name}'

    def days_left(self):
        today_date = datetime.date.today()
        days_left = (self.release_date - today_date)
        return days_left.days

    def match_release(self):

        if AlbumModel.objects.filter(release_date=self.release_date, artist_name__in=self.artist_name.all()).exists():
            self.album = AlbumModel.objects.get(release_date=self.release_date, artist_name__in=self.artist_name.all())
            self.save()
            return True
        else:
            self.album = None
            return False


class AlbumModel(models.Model):
    artist_name = models.ManyToManyField(
        ArtistModel,
        related_name='albums',
        related_query_name='album',
    )
    name = models.CharField(max_length=200, unique=False)
    cover64 = models.CharField(max_length=150)
    cover300 = models.CharField(max_length=150)
    cover640 = models.CharField(max_length=150)
    link = models.CharField(max_length=150)
    spotify_id = models.CharField(max_length=100, blank=True)
    release_date = models.DateField()
    total_tracks = models.SmallIntegerField(null=True, blank=True)
    album_type = models.CharField(max_length=30, null=True, blank=True)
    album_songs_sting = models.CharField(max_length=2000, null=True, blank=True)

    class Meta:
        ordering = ["-release_date"]

    def uri(self):
        return self.link.split('/')[-1]

    def artists(self):
        artists_name = self.artist_name.all()
        artists_string = []
        for artist in artists_name:
            artists_string.append(artist.name)
        return ", ".join(artists_string)

    def give_app_link(self):
        return f'spotify:album:{self.uri()}'

    def give_likes_count(self):
        from profile_page.models import LikeModel
        return LikeModel.objects.filter(album=self).count()


    def __str__(self):
        return f"{self.name}"


class SongModel(models.Model):
    name = models.CharField(max_length=200)
    track_number = models.SmallIntegerField(null=True, blank=True)
    spotify_id = models.CharField(max_length=50, unique=True, default='5mc6EyF1OIEOhAkD0Gg9Lc')
    album = models.ForeignKey(
        AlbumModel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='songs',
        related_query_name='song'
    )
    artist = models.ManyToManyField(
        ArtistModel,
        related_name='songs',
        related_query_name='song'
    )

    def artists(self):
        artists_name = self.artist.all()
        artists_string = []
        for artist in artists_name:
            artists_string.append(artist.name)
        return ", ".join(artists_string)

    def __str__(self):
        return f'{self.name}'

    class Meta:
        verbose_name = 'Song'
        verbose_name_plural = 'Songs'
        ordering = ['album', 'track_number']



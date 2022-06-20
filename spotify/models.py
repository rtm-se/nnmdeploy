from django.db import models
from django.contrib.auth.models import User


# Create your models here.


class SpotifyToken(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    access_token = models.CharField(max_length=500)
    refresh_token = models.CharField(max_length=500)
    expires_in = models.DateTimeField()
    token_type = models.CharField(max_length=50, default='Bearer')


class SpotifyProfile(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    display_name = models.CharField(max_length=300)
    spotify_id = models.CharField(max_length=100)
    external_urls = models.CharField(max_length=300)
    images = models.CharField(max_length=300, null=True, blank=True)

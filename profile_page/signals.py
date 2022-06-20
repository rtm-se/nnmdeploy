from django.db.models.signals import pre_delete
from django.contrib.auth.models import User

from profile_page.models import EncounteredAlbumModel, WaitingListAlbumModel, ReviewModel,\
    ProfileModel, LikeModel, ListenedSongsModel, RecommendationModel,\
    SpotifyLikeModel, SpotifySavedAlbumModerl

from spotify.models import SpotifyToken, SpotifyProfile

def user_deletion_handler(sender, instance, using, **kwargs):
    #if kwargs['raw']:
    #    return
    print(f'Init {instance.username} data delete')
    EncounteredAlbumModel.objects.filter(user=instance).delete()
    WaitingListAlbumModel.objects.filter(user=instance).delete()
    ReviewModel.objects.filter(user=instance).delete()
    ProfileModel.objects.filter(user=instance).delete()
    LikeModel.objects.filter(user=instance).delete()
    ListenedSongsModel.objects.filter(user=instance).delete()
    RecommendationModel.objects.filter(user=instance).delete()
    SpotifyLikeModel.objects.filter(user=instance).delete()
    SpotifySavedAlbumModerl.objects.filter(user=instance).delete()
    SpotifyToken.objects.filter(user=instance).delete()
    SpotifyProfile.objects.filter(user=instance).delete()

pre_delete.connect(user_deletion_handler, sender=User)
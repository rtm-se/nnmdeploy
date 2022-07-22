import logging
from django.contrib.auth.models import User
from celery import shared_task
from .get_recently_played_tracks import get_recent_tracks

@shared_task
def recent_tracks(user_id):
    get_recent_tracks(user_id)
    return True


@shared_task
def update_users_data():
    subscribed_users_ids = User.objects.filter(spotifytoken__token_type='Bearer').values_list('id', flat=True)
    for user_id in subscribed_users_ids:
        try:
            get_recent_tracks(user_id)
        except:
            logging.error(f'user {user_id} failed to update, check logs')

@shared_task
def debug_spotify():
    print('bruh')

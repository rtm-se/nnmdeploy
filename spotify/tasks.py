from celery import shared_task
from .get_recently_played_tracks import get_recent_tracks

@shared_task
def recent_tracks(user_id):
    get_recent_tracks(user_id)
    return True

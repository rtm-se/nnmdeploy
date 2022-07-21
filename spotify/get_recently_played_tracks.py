import logging

import requests

from .util import is_spotify_authenticated
from .spotify_api_data_handlers import SpotifyDataHandler
from django.contrib.auth.models import User
from profile_page.models import ListenedSongsModel, EncounteredAlbumModel
from main_page.models import SongModel, AlbumModel
from spotify.models import SpotifyToken

AFTER = 1484811043508


def get_recent_tracks(user_id):
    user = User.objects.get(id=user_id)
    logging.basicConfig(level=logging.INFO)
    logging.warning(f'getting recent tracks for {user}')
    # Check/update the expiration for tokens
    # Verify auth
    is_spotify_authenticated(user)
    # Get keys
    tokens = SpotifyToken.objects.get(user=user)
    # Get oauth_token
    oauth_token: str = tokens.access_token
    # Make request
    response_data: dict = get_recent_songs_data(oauth_token)
    # Clean up already processed data
    new_data = clean_up_data_with_date(response_data, user)
    if not new_data:
        logging.warning(f'end of recent songs update for {user} no new data')
        return True
    # Feed the data to handler to create missing models
    # Making sure to feed data handler only songs objects
    new_data_only_songs = [item['track'] for item in new_data]
    spotify_dh = SpotifyDataHandler(new_data_only_songs, 'song')
    # create listened_songs and encountered_albums entries
    create_listened_songs(new_data, user, spotify_dh.songs)
    add_new_encountered_albums(spotify_dh.albums, user)
    update_encountered_completion(spotify_dh.albums, user)
    logging.warning(f'end of recent songs update for {user} with new data')
    return True


def get_recent_songs_data(key) -> dict:
    # Staging data for a request
    payload: dict = {'limit': 50, 'after': AFTER, }
    headers: dict = {'Authorization': f'Bearer    {key}'}
    link: str = 'https://api.spotify.com/v1/me/player/recently-played'
    # Making a request
    request = requests.get(link, params=payload, headers=headers)
    # Checking for a response code and printing the raising error in case the status code is not 200(success)
    if request.status_code != 200:
        raise Exception(f'recent songs data request failed with code {request.status_code} \n {request.json()}')

    #  logging a request
    # with open(
    #   f'logs/{datetime.datetime.now().strftime("%d-%m-%Y--%H-%M-%S")}-{key[10:20]}', 'x', encoding="utf-8"
    #   ) as file:
    #    file.write(f'{request.status_code}, \n {request.text}, \n {request.content}')

    # Converting json to dict
    response_data: dict = request.json()
    return response_data


def clean_up_data_with_date(response_data: dict, user):
    list_of_dates: list[str] = []
    # Dumping all of the dates into the list to make a query call
    for item in response_data['items']:
        list_of_dates.append(item['played_at'])
    # Geting a list of matching values
    matching_dates = list(ListenedSongsModel.objects.filter(
        user=user, played_at__in=list_of_dates
    ).values_list('played_at', flat=True))
    # Getting differences between two lists
    unmatched_dates = set(list_of_dates) - set(matching_dates)
    # Checking if there are items to process
    if len(unmatched_dates):
        # Creating new list of entries that didn't have matched dates
        new_data = [item for item in response_data['items'] if item['played_at'] in unmatched_dates]
        return new_data
    else:
        return False


def create_listened_songs(items_data: list, user, dict_of_song) -> None:
    list_of_objects_to_create: list = []
    for item in items_data:
        song = dict_of_song[item['track']['id']]['obj']
        list_of_objects_to_create.append(ListenedSongsModel(
            played_at=item['played_at'],
            user=user,
            song=song
        ))
    ListenedSongsModel.objects.bulk_create(list_of_objects_to_create)


def add_new_encountered_albums(albums_dict: dict, user) -> None:
    encountered_to_create: list = []
    albums_ids = albums_dict.keys()
    recorded_ids = list(EncounteredAlbumModel.objects.filter(
        user=user, album__spotify_id__in=albums_ids
    ).values_list('album__spotify_id', flat=True))
    unrecorded_ids = set(albums_ids) - set(recorded_ids)
    logging.warning(unrecorded_ids)
    for album_id in unrecorded_ids:
        album = albums_dict[album_id]['obj']
        encountered_to_create.append(
            EncounteredAlbumModel(
                user=user,
                album=album
            )
        )

    EncounteredAlbumModel.objects.bulk_create(encountered_to_create)


def update_encountered_completion(data_handler_list: dict, user) -> bool:
    if data_handler_list is None:
        return False
    encountered_albums = EncounteredAlbumModel.objects.filter(user=user, album__spotify_id__in=data_handler_list.keys())
    for entry in encountered_albums:
        entry.get_song_completion()
    return True

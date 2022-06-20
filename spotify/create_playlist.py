import random
import datetime
import time

import requests
from .models import SpotifyToken, SpotifyProfile
from .util import is_spotify_authenticated
from profile_page.models import EncounteredAlbumModel as ListenedAlbumModel



def create_playlist(user, albums_q, shuffle, page):
    #get a token
    is_spotify_authenticated(user=user)

    tokens = SpotifyToken.objects.get(user=user)

    #get the list of albums for a user
    #old method
    #albums = ListenedAlbumModel.objects.filter(user=user, album__release_date__gte=datetime.date(2020, 1, 1))

    if page == 'playlist':
        # get ids from album models
        uris = get_albums_uri_model(albums_q)
    else:
        #get uri for each album for many to many related q
        uris = get_albums_uri_q(albums_q)
    #get list of songs for each album
    song_uri_list = get_songs_uri(uris, tokens.access_token)
    # create playlist
    playlist_data = create_empty_playlist(user, tokens.access_token, page)
    # add songs to playlist
    if len(song_uri_list) > 100:
        several_requests = True
        splited_song_uri_list = split_list(song_uri_list)
    #todo make a verification for length of the lists + split the list of added album tracks if it exeeds the spotify one time song addition
    if shuffle:
        random.shuffle(song_uri_list)
        add_song_to_playlist(song_uri_list[0:30], playlist_data['playlist_id'], tokens.access_token)
    elif several_requests:
        for part in splited_song_uri_list:
            add_song_to_playlist(part, playlist_data['playlist_id'], tokens.access_token)
    else:
        add_song_to_playlist(song_uri_list, playlist_data['playlist_id'], tokens.access_token)
    return playlist_data['playlist_link']


def get_songs_uri(uris, access_token):
    songs_uris = []
    for album_id in uris:
        link = f"https://api.spotify.com/v1/albums/{album_id}/tracks"
        params = {
            "market": 'US',
            'limit': 30,
            'offset': 0
            }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(link, params=params, headers=headers)
        data_dict = response.json()
        time.sleep(2)
        items = data_dict['items']
        for song in items:
            songs_uris.append(song['uri'])

    return songs_uris

#todo fix this use shell
def get_albums_uri_q(album_list):
    album_uris = []
    for object in album_list:
        album_uris.append(object.album.uri())
    return album_uris


def get_albums_uri_model(album_list):
    albums_uris = []
    for album in album_list:
        albums_uris.append(album.uri())
    return albums_uris


def create_empty_playlist(user, access_token, page):
    spotify_id = SpotifyProfile.objects.get(user=user).spotify_id

    link = f'https://api.spotify.com/v1/users/{spotify_id}/playlists'
    if page == 'like':
       name = "NoNM's likes playlist "
    elif page == 'new':
        name = "NoNM's new albums playlist "
    elif page == 'playlist':
        name = f"NoNW's {user.username} playlist"
    else:
        name = "NoNM's playlist"
    body = {
        "name": name,
        "description": "New playlist description",
        "public": False
        }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
        }
    response = requests.post(link, json=body , headers=headers)

    data_dict = response.json()
    playlist_id = data_dict['id']
    playlist_link = "https://open.spotify.com/playlist/" + playlist_id

    playlist_data = {
        'playlist_id': playlist_id,
        'playlist_link': playlist_link
    }

    return playlist_data


def add_song_to_playlist(song_uris, playlist_id, access_token):
    link = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'

    data = {
        'uris': ','.join(song_uris)
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
        }

    requests.post(link, params=data, headers=headers)


def split_list(uris):
    list_of_slices = []
    length = len(uris)
    slices_count = length//100
    float_point = length % 100
    counter = 0
    while slices_count > counter:
        list_of_slices.append(uris[counter*100:counter*100+100])
        counter += 1

    if float_point:
        list_of_slices.append(uris[slices_count*100:length])

    return list_of_slices



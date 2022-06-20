import requests
from spotify.models import SpotifyToken
from .record_likes import slice_the_querry


def put_spotify_saved_albums(user, querry):
    tokens = SpotifyToken.objects.get(user=user)
    albums_sliced = slice_the_querry(querry)
    for part in albums_sliced:
        string_of_ids = stringify_albums(part)
        status = record_albums_request(tokens.access_token, string_of_ids)
        print(status)
    return True


def stringify_albums(list_of_albums):
    list_of_strings = []
    for pair in list_of_albums:
        list_of_strings.append(pair.album.uri())
    string_of_uris = ','.join(list_of_strings)
    return string_of_uris


def record_albums_request(key, string_of_ids):
    url = 'https://api.spotify.com/v1/me/albums'
    json = {
        'ids': string_of_ids
    }
    headers = {
        'Accept': 'application / json',
        "Content-Type": "application/json",
        'Authorization': f'Bearer    {key}'
    }

    response = requests.put(url, params=json, headers=headers)
    return response.status_code

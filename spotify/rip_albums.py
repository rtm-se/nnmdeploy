import requests
from profile_page.models import SpotifySavedAlbumModerl
from spotify.models import SpotifyToken
from spotify import spotify_request_script

def rip_albums(user):
    tokens = SpotifyToken.objects.get(user=user)
    all_albums_list = []
    next_check = True
    counter = 0
    while next_check:
        #getting access_tokens data
        data = rip_album_request(offset=counter, key=tokens.access_token)
        next_check = data['next']
        counter += 1
        #parsong data
        nodes = album_json_parser(data)

        # adding new artists to db
        spotify_request_script.add_artists_to_db(nodes[0])
        #add albums to db and return list of reference objects
        list_of_album_models = spotify_request_script.add_albums_to_db(nodes[1])
        # user reference objects from added albums to add new connection between user and an album as a saved album
        add_spotifysavedalbums(user=user, list_of_albums_models=list_of_album_models)
        # adding album to listened albums
        spotify_request_script.add_listened_albums(user=user, list_of_album_models=list_of_album_models)



    return data['total']


def rip_album_request(key, offset):
    url = 'https://api.spotify.com/v1/me/albums'
    payload = {
        'market': 'US',
        'limit': 50,
        'offset': f'{offset * 49}'
    }
    headers = {
        'Accept': 'application / json',
        "Content-Type": "application/json",
        'Authorization': f'Bearer    {key}'
    }
    response = requests.get(url, params=payload, headers=headers)

    data = response.json()
    return data


def album_json_parser(dict_request):
    for item in dict_request['items']:
        # name, artist_link, album, cover, album_link, date, song

        # artist
        artist_name = item['album']['artists'][0]['name']
        artist_link = item['album']['artists'][0]['external_urls']['spotify']

        spotify_request_script.SpotifyArtistNode(artist_name=artist_name, artist_link=artist_link)

        # album
        album_name = item['album']['name']
        album_cover64 = item['album']['images'][2]['url']
        album_cover300 = item['album']['images'][1]['url']
        album_cover640 = item['album']['images'][0]['url']
        album_link = item['album']['external_urls']['spotify']
        total_tracks = item['album']['total_tracks']
        album_type = item['album']['album_type']

        if item['album']['release_date_precision'] == "year":
            album_date = item['album']['release_date'] + '-01-01'
        elif item['album']['release_date_precision'] == "month":
            album_date = item['album']['release_date'] + '-01'
        else:
            album_date = item['album']['release_date']

        spotify_request_script.SpotifyAlbumNode(artist_name=artist_name, album_name=album_name, cover64=album_cover64, cover300=album_cover300,
                         cover640=album_cover640,  album_link=album_link, date=album_date, total_tracks=total_tracks,
                         album_type=album_type)



    nodes = [
            spotify_request_script.SpotifyArtistNode.ListOfNodes,
            spotify_request_script.SpotifyAlbumNode.ListOfNodes,
        ]

    return nodes


def add_spotifysavedalbums(user, list_of_albums_models):
    for album in list_of_albums_models:
        if not SpotifySavedAlbumModerl.objects.filter(album=album).exists():
            obj = SpotifySavedAlbumModerl(user=user, album=album)
            obj.save()
    return True


if __name__ == '__main__':
    pass
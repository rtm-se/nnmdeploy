import difflib
import datetime
from random import choice, shuffle, choices
import requests
from .util import is_spotify_authenticated
from .models import SpotifyToken
from main_page.models import SongModel, ArtistModel
from profile_page.models import ProfileModel, LikeModel, RecommendationModel, EncounteredAlbumModel
from spotify import spotify_request_script

simple_genre_seeds = ["blues", "indie", "rock", "pop", "jazz", "r-n-b"]

genre_seeds = ["acoustic", "afrobeat", "alt-rock", "alternative", "ambient", "black-metal", "bluegrass",
               "blues",
               "bossanova", "breakbeat", "chicago-house", "chill",
               "classical",
               "club", "comedy", "country", "dance", "dancehall", "death-metal", "deep-house", "detroit-techno",
               "disco",
               "drum-and-bass", "dub", "dubstep", "edm", "electro", "electronic", "emo", "folk", "forro",
               "funk", "garage", "gospel", "goth", "grindcore", "groove", "grunge", "guitar", "happy",
               "hard-rock",
               "hardcore", "hardstyle", "heavy-metal", "hip-hop", "holidays", "honky-tonk", "house", "idm",
               "indie",
               "indie-pop", "industrial", "j-pop", "j-rock", "jazz", "k-pop", "malay", "mandopop", "metal",
               "metal-misc", "metalcore", "minimal-techno", "mpb",
               "new-age",
               "new-release", "opera", "pagode", "party", "piano", "pop", "post-dubstep",
               "power-pop", "progressive-house", "psych-rock", "punk", "punk-rock", "r-n-b", "rainy-day", "reggae",
               "reggaeton", "road-trip", "rock", "rock-n-roll", "rockabilly", "romance", "sad", "salsa", "samba",
               "sertanejo",
               "show-tunes", "singer-songwriter", "ska", "sleep", "songwriter", "soul", "study",
               "summer", "synth-pop", "tango", "techno", "trance", "trip-hop", "work-out",
               "world-music"
               ]


def make_recommendations(user):
    # get tokens
    if not is_spotify_authenticated(user=user):
        return False
    tokens = SpotifyToken.objects.get(user=user)
    # get an obsession
    profile = ProfileModel.objects.get(user=user)

    favorite_album = profile.favorite_album

    album_models_list = []

    # get albums to a list

    if favorite_album:
        album_models_list.append(favorite_album)

        albums = LikeModel.objects.filter(user=user).exclude(album=favorite_album)
        if albums.exists():
            album = choice(albums)
            album_models_list.append(album.album)
    else:
        albums = LikeModel.objects.filet(user=user)
        if albums.exists() and len(albums) > 1:
            album_models_list = choices(albums, k=2)
            real_album_models = []
            for album in album_models_list:
                real_album_models.append(album.album)
            album_models_list = real_album_models
        else:
            # adding choice as to extract album from the querry
            album_models_list.append(choice(albums[0].album))

    # getting songs
    song_ids_sting = songs_ids_from_albums(album_models_list, tokens.access_token)

    # get artists models
    artists_models_list = []
    for album in album_models_list:
        artists_models_list.append(album.artist_name.all()[0])

    # get their uris
    # possibly reduce the sting
    artists_ids_list = []
    if len(artists_models_list) > 1:
        for artist in artists_models_list:
            id = artist.give_uri()
            artists_ids_list.append(id)
        artists_ids_list = ','.join(artists_ids_list)
    else:
        artists_ids_list = artists_models_list[0].give_uri()

    # get genres

    #genres_string = get_genres_from_artists_models(artists_models_list)
    #genres_string = choice(simple_genre_seeds)
    genres_string = get_genres_from_artists_models(artists_models_list=artists_models_list, key=tokens.access_token)
    genres_string = choice(genres_string)
    # request the recommendations
    # parse recomendations
    nodes = get_albums_recommendations(tokens.access_token, song_ids_sting, artists_ids_list, genres_string, 10)

    # add new artists to db
    spotify_request_script.add_artists_to_db(nodes[0])
    # add new albums to db
    list_of_album_models = spotify_request_script.add_albums_to_db(nodes[1])
    # add to a wrapper for ease of use and later reuse
    add_to_recommendations(album_list=list_of_album_models, user=user)
    # return list of albums
    return True


def get_several_artists(artists_ids_string, key):
    payload = {
        'ids': artists_ids_string
    }
    headers = {
        'Accept': 'application / json',
        "Content-Type": "application/json",
        'Authorization': f'Bearer    {key}'
    }
    link = 'https://api.spotify.com/v1/artists'
    request = requests.get(link, params=payload, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        return None


def parsing_data_from_artists_request(data):
    artists = []
    for artist in data['artists']:
        #getting the right model
        artists_model = ArtistModel.objects.get(artist_link=artist['external_urls']['spotify'])
        if len(artist['genres']) < 1:
            genres_string = 'empty'
        else:
            genres_string = ','.join(artist['genres'])
        artists_model.genres = genres_string
        artists_model.save(update_fields=["genres"])
        artists.append(artists_model)
    return artists


# get clean string of genres for recommendations request as well as trying to get genres for artist models
def get_genres_from_artists_models(artists_models_list, key):
    request_list = []
    list_of_genres = []
    for artist in artists_models_list:
        if artist.genres is None:
            request_list.append(artists_models_list.pop(artists_models_list.index(artist)))

    if request_list:
        list_of_ids = [artist.give_uri() for artist in request_list]
        if len(list_of_ids) > 1:
            list_of_ids = ','.join(list_of_ids)
        data = get_several_artists(list_of_ids, key)
        for model in parsing_data_from_artists_request(data):
            artists_models_list.append(model)

    for artist in artists_models_list:

        if artist.genres == 'empty':
            list_of_genres.append(choice(simple_genre_seeds))
        else:
            for genre in artist.genres.split(','):
                list_of_genres.append(genre)

    cleaned_genres_all = clean_genres(list_of_genres)

    if cleaned_genres_all is None:
        cleaned_genres_all = choice(simple_genre_seeds)
    return cleaned_genres_all

# get_several_album request that will provide 2 songs in a string
def get_several_album(list_of_albums, key):
    payload = {
        'ids': list_of_albums,
        'market': 'US'
    }
    headers = {
        'Accept': 'application / json',
        "Content-Type": "application/json",
        'Authorization': f'Bearer    {key}'
    }
    link = 'https://api.spotify.com/v1/albums'
    request = requests.get(link, params=payload, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        return False


def make_sting_songs_ids_from_request(data):
    songs_list = []
    for album in data['albums']:
        track = choice(album['tracks']['items'])
        songs_list.append(track['id'])

    return songs_list


def songs_ids_from_albums(list_of_album_models, key):
    songs_ids = []
    list_for_request = []
    for album in list_of_album_models:
        # checking if there are songs from onsite db for that album, choose a random one for a seed
        songs = SongModel.objects.filter(album=album)
        if songs.exists():
            song = choice(songs)
            songs_ids.append(song.spotify_id)

        else:
            # if no songs for the album add album to list of albums that are going to make a request
            list_for_request.append(album)

    # if there are models in request list make a request for several albums
    if list_for_request:
        albums_ids_string = []
        for album in list_for_request:
            albums_ids_string.append(album.uri())

        if len(albums_ids_string) > 1:
            albums_ids_string = ','.join(albums_ids_string)
        request_data = get_several_album(albums_ids_string, key)
        songs_ids = make_sting_songs_ids_from_request(request_data)
        for song_id in songs_ids:
            # will it append letter by letter if there will be only one song in a list?
            list_for_request.append(song_id)

    # check for edge case where's there's only 1 song from 1 album
    if len(list_for_request) > 1:
        list_for_request = ','.join(list_for_request)

        return list_for_request


def get_a_song(album_uri, key):
    payload = {
        'market': 'US',
        'limit': 20,
        'offset': 0
    }
    headers = {
        'Accept': 'application / json',
        "Content-Type": "application/json",
        'Authorization': f'Bearer    {key}'
    }
    link = f'https://api.spotify.com/v1/albums/{album_uri}/tracks'
    request = requests.get(link, params=payload, headers=headers)
    items = request.json()['items']
    item = choice(items)
    return item['uri'].split(':')[-1]


def get_genre(artist_uri, key):
    headers = {
        'Accept': 'application / json',
        "Content-Type": "application/json",
        'Authorization': f'Bearer    {key}'
    }
    link = f'https://api.spotify.com/v1/artists/{artist_uri}'
    request = requests.get(link, headers=headers)
    if request.status_code == 200:
        genres = request.json()['genres']
        return genres
    else:
        print(request.status_code)
        return f'False {request.status_code}'


def clean_genres(genres):
    results = []
    for genre in genres:
        semi_result = difflib.get_close_matches(genre, genre_seeds)
        if semi_result:
            results.append(semi_result[0])
        else:
            if len(genre.split(' ')) > 1:
                semi_result = difflib.get_close_matches(genre[genre.index(' '):], genre_seeds)
                if semi_result:
                    for result in semi_result:
                        results.append(result)

    if results:
        return results
    else:
        return None


def request_recommendations(key, song_seed, artist_seed, genres_string, popularity):
    headers = {
        'Accept': 'application / json',
        "Content-Type": "application/json",
        'Authorization': f'Bearer    {key}'
    }
    payload = {
        'limit': 30,
        'market': 'US',
        'seed_artists': artist_seed,
        'seed_genres': genres_string,
        'seed_tracks': song_seed,
        'min_popularity': popularity,
        'target_popularity': popularity + 10
    }
    link = 'https://api.spotify.com/v1/recommendations'
    request = requests.get(link, params=payload, headers=headers)
    results = request.json()['tracks']
    return results


# todo check for existing model before creating node
def parse_recommendations(results):
    compare_to = datetime.datetime(2019, 12, 31)
    for item in results:
        if item['album']['release_date_precision'] == 'year':
            album_date = item['album']['release_date'] + '-01-01'
        elif item['album']['release_date_precision'] == "month":
            album_date = item['album']['release_date'] + '-01'
        else:
            album_date = item['album']['release_date']



        if datetime.datetime.strptime(album_date, '%Y-%m-%d') > compare_to:
            artist_name = item['artists'][0]['name']
            artist_link = item['artists'][0]['external_urls']['spotify']

            spotify_request_script.SpotifyArtistNode(artist_name=artist_name, artist_link=artist_link)

            # album
            album_name = item['album']['name']
            album_cover640 = item['album']['images'][0]['url']
            album_cover300 = item['album']['images'][1]['url']
            album_cover64 = item['album']['images'][2]['url']
            album_link = item['album']['external_urls']['spotify']
            total_tracks = item['album']['total_tracks']
            album_type = item['album']['album_type']

            spotify_request_script.SpotifyAlbumNode(
                artist_name=artist_name, album_name=album_name,
                cover64=album_cover64, cover300=album_cover300,
                cover640=album_cover640, album_link=album_link,
                date=album_date, total_tracks=total_tracks,
                album_type=album_type)

        nodes = [
            spotify_request_script.SpotifyArtistNode.ListOfNodes,
            spotify_request_script.SpotifyAlbumNode.ListOfNodes,
        ]
        return nodes


def get_albums_recommendations(key, song_seed, artist_seed, genres, popularity):
    genres_string = clean_genres(genres)
    #if not genres_string:
    #    return 'no_genres'
    result = [[], []]
    while len(result[1]) <= 5:
        results = request_recommendations(key, song_seed, artist_seed, genres, popularity)
        result = parse_recommendations(results)
        if result is None:
            result = [[], []]
        popularity += 10
        if popularity > 100:
            return result
    return result


def add_to_recommendations(album_list, user):
    recommendations_list = []
    for album in album_list:
        if not RecommendationModel.objects.filter(user=user, album=album).exists() and not LikeModel.objects.filter(
                user=user, album=album).exists() and not EncounteredAlbumModel.objects.filter(user=user,
                                                                                              album=album).exists():
            recommendation = RecommendationModel(user=user, album=album)
            recommendation.save()
            recommendations_list.append(recommendation)

    return recommendations_list

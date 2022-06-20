from django.db.models import Q
import requests
from main_page.models import SongModel, ArtistModel, AlbumModel


def split_list(list_to_split: list[str], segment_size: int ) -> list[list[str]]:
    list_of_slices: list = []
    length: int = len(list_to_split)
    slices_count = length // segment_size
    float_point = length % segment_size
    counter = 0
    while slices_count > counter:
        list_of_slices.append(list_to_split[counter * segment_size:counter * segment_size + segment_size])
        counter += 1

    if float_point:
        list_of_slices.append(list_to_split[slices_count * segment_size:length])

    return list_of_slices


def make_get_songs_request(segment, user_key) -> dict:
    url = 'https://api.spotify.com/v1/tracks'
    headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {user_key}"
    }
    data = {
        "market": 'US',
        "ids": ",".join(segment)
    }
    response = requests.get(url, params=data, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(response.json(), response)


def fill_missing_fields(item, song_model_object):

    print(f'updating artists on {song_model_object}')
    for artist in item['artists']:
        if ArtistModel.objects.filter(artist_link=artist['external_urls']['spotify']).exists():
            artists_object = ArtistModel.objects.get(artist_link=artist['external_urls']['spotify'])
            song_model_object.artist.add(artists_object)
        else:
            print(f"artist doesn\'t exist {artist['name']}")
            print(f"artist's link {artist['external_urls']['spotify']}")
    if song_model_object.album is None:
        print(f'updating album on {song_model_object}')
        if AlbumModel.objects.filter(link=item['album']['external_urls']['spotify']).exists():
            album_object = AlbumModel.objects.get(link=item['album']['external_urls']['spotify'])
            song_model_object.album = album_object
        else:
            print(f"album doesn\'t exist {item['album']['name']}")
            print(f"album link  {item['album']['external_urls']['spotify']}")
    song_model_object.save()


def update_songs() -> None:
    songs = SongModel.objects.filter(Q(artist=None)|Q(album=None))
    [song for song in songs]
    lis_of_ids: list[str] = []
    for song in songs:
        lis_of_ids.append(song.spotify_id)
    
    if len(lis_of_ids) > 50:
        splited_list_of_ids = split_list(list(set(lis_of_ids)), 10)
    else:
        splited_list_of_ids = [lis_of_ids, ]

    user_key = input('please insert user id:\n')
    for segment in splited_list_of_ids:
        response = make_get_songs_request(segment, user_key)
        for item in response['tracks']:
            if songs.filter(spotify_id=item['id']).exists():
                song = songs.filter(spotify_id=item['id'])[0]
                fill_missing_fields(item, song)
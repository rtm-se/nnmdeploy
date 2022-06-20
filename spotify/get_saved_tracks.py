from requests import get
from .util import is_spotify_authenticated
from spotify.models import SpotifyToken
from profile_page.models import ListenedSongsModel, SpotifyLikeModel
from .spotify_api_data_handlers import SpotifyDataHandler


def get_saved_tracks(user):
    pass
    # Verify auth
    is_spotify_authenticated(user)
    # Get keys
    tokens = SpotifyToken.objects.get(user=user)
    # Get oauth_token
    oauth_token: str = tokens.access_token
    # Make requests
    data_set: list = get_saved_songs(oauth_token)
    # Clean data with dates of last listened songs most likely redundant
    data_set_first_wash: list = clean_data_with_date(data_set, user)
    # Clean data with songs that are already recorded
    data_set_second_wash: list = clean_data_with_spotify_ids(data_set_first_wash, user)
    # Make a list of tracks only
    data_tracks_only: list = [item['track'] for item in data_set_second_wash]
    # Feed the data to api data handler for creating missing song models
    spotify_dh = SpotifyDataHandler(data_tracks_only, 'song')
    # Record new songs as saved track models and listened songs models
    songs = create_listened_songs_and_spotify_like_models(data_set_second_wash, user, spotify_dh.songs)
    return songs


def get_saved_songs(oauth_token: str, **kwargs) -> list[dict]:
    # Function that makes request to spotify and gets the saved songs into a list of dictionary items
    # Staging data to make a request
    url: str = 'https://api.spotify.com/v1/me/tracks'
    params: dict = {
        'limit': 50
    }
    headers: dict = {
        'Accept': 'application / json',
        "Content-Type": "application/json",
        'Authorization': f'Bearer    {oauth_token}'
    }
    # Checking if it's a recursive call and if we need to offset the starting position of the response
    if 'next' in kwargs:
        params.update({'offset': kwargs['next']})

    # Making a get request
    response = get(url=url, params=params, headers=headers)
    # Checking for status code in response
    if not response.status_code == 200:
        raise Exception(f'response code is not 200\n {response.json()}')

    # Getting dictionary data from response
    data_dict: dict = response.json()

    # making a recursive call if there are more than 50 items
    if data_dict['next'] is None:
        # Base Case

        return data_dict['items']
    else:
        # Making another call

        # Getting the offset for the next call
        next_link: str = data_dict['next']
        offset: int = int(next_link.split('&')[0].split('=')[1])
        # Next call
        after_request_list: list = get_saved_songs(oauth_token, next=offset)
        # Combining the response items with previous
        complete_list: list[dict] = data_dict['items'] + after_request_list
        return complete_list


def clean_data_with_date(data_set, user):
    # Function that will remove any data items with the dates already in last listen songs by the user
    # Get all the dates from data set
    dates_from_data_set: set[str] = {item['added_at'] for item in data_set}
    # Making a query for matching dates and storing only matched ones in the set
    matched_dates = set(
        ListenedSongsModel.objects.filter(
            user=user,
            played_at__in=dates_from_data_set
        ).values_list('played_at', flat=True)
    )
    # Calculating the unmatched dates
    unmatched_dates: set = set(dates_from_data_set) - matched_dates
    # Getting the items with the unmatched date
    cleaned_data_set: list = [item for item in data_set if item['added_at'] in unmatched_dates]
    return cleaned_data_set


def clean_data_with_spotify_ids(data_set, user):
    # Function that will remove any data items if said item have the song id already in the list of saved track
    # Making a set of songs spotify ids from data set
    song_ids: set = {item['track']['id'] for item in data_set}
    # Getting matched ids into set
    matched_ids: set = set(
        SpotifyLikeModel.objects.filter(
            user=user,
            song__spotify_id__in=song_ids
        ).values_list('song__spotify_id', flat=True)
    )
    # Calculating unmatched ids
    unmatched_ids: set = song_ids - matched_ids
    # Cleaning data set
    cleaned_data_set: list = [item for item in data_set if item['track']['id'] in unmatched_ids]
    return cleaned_data_set


def create_listened_songs_and_spotify_like_models(items_data: list, user, dict_of_song) -> list:
    list_of_objects_to_create_listened: list = []
    list_of_objects_to_create_spotify_like: list = []
    list_of_songs: list = []
    for item in items_data:
        song = dict_of_song[item['track']['id']]['obj']
        list_of_objects_to_create_listened.append(ListenedSongsModel(
            played_at=item['added_at'],
            user=user,
            song=song
        ))
        list_of_objects_to_create_spotify_like.append(SpotifyLikeModel(
            user=user,
            song=song
        ))
        list_of_songs.append(song)
    ListenedSongsModel.objects.bulk_create(list_of_objects_to_create_listened)
    SpotifyLikeModel.objects.bulk_create(list_of_objects_to_create_spotify_like)
    return list_of_songs
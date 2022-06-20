from requests import get
from django.contrib.auth.models import User
from main_page.models import ArtistModel
from profile_page.models import SpotifyFollowedArtistModel, ProfileModel
from spotify.models import SpotifyToken
from .util import is_spotify_authenticated


def record_followed_artists(user):
    # Verify auth
    is_spotify_authenticated(user)
    # Get keys
    tokens = SpotifyToken.objects.get(user=user)
    oauth_token: str = tokens.access_token
    # Make requests
    list_of_artists_date: list[dict] = get_artists(oauth_token)
    # Find/create models from db
    matched_artists_models = math_spotify_data_to_artist_model(list_of_artists_date)
    # exclude_artists_models that are already registered for that user
    excluded_models = matched_artists_models.exclude(SpotifyFollowedArtist__user=user)
    # create spotify followed models
    create_followed_models(excluded_models, user)

    return excluded_models

def get_artists(oauth_token: str, **kwargs) -> list[dict]:
    # Function that makes request to spotify and gets the followed artists in a list of dictionary items
    url: str = 'https://api.spotify.com/v1/me/following'

    headers: dict = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {oauth_token}"
    }

    params: dict = {
        'type': 'artist',
        'limit': 50
    }
    # Checking if it's a recursive call and if we need to offset the starting position of the response
    if 'after' in kwargs:
        params.update({'after': kwargs['after']})

    # Making a get request
    response = get(url=url, params=params, headers=headers)
    # Checking for status code in response
    if not response.status_code == 200:
        raise Exception(f'response code is not 200\n {response.json()}')

    # Getting dictionary data from response
    data_dict: dict = response.json()

    # making a recursive call if there are more then 50 artists
    if data_dict['artists']['next'] is None:
        # Base Case
        return data_dict['artists']['items']
    else:
        # Making another call
        link_to_next_request: str = data_dict['artists']['next']
        # Getting the artists spotify id that will offset the start of the list
        after: str = link_to_next_request.split('&')[1].split('=')[1]

        after_request_list: dict = get_artists(oauth_token, after=after)
        # Combinging the response artists with previous
        complete_list: list[dict] = data_dict['artists']['items'] + after_request_list
        return complete_list


def create_artist_model(artists_data: dict) -> ArtistModel:
    # Creating an artists model from data received from spotify
    name: str = artists_data['name']
    artists_link: str = artists_data['external_urls']['spotify']
    genres: str = ','.join(artists_data['genres'])
    artist = ArtistModel(
        name=name,
        artist_link=artists_link,
        genres=genres
    )
    return artist


def math_spotify_data_to_artist_model(artists_data: list[dict]) -> list[ArtistModel]:
    # Get models from db and create missing ones.
    # Getting all link with unique modifiers from dictionary elemets
    list_of_spotify_links: list[str] = []
    for artist in artists_data:
        list_of_spotify_links.append(artist['external_urls']['spotify'])
    matched_artsits_models = ArtistModel.objects.filter(artist_link__in=list_of_spotify_links).only('id', 'artist_link')

    # Populating cache
    [artist for artist in matched_artsits_models]

    found_models_count: int = matched_artsits_models.count()
    # Checking if all the models are in place
    if len(artists_data) == found_models_count:
        return matched_artsits_models
    else:
        # Creating the missing models
        artists_models_to_create: list[ArtistModel] = []
        # Checking if there are models found at all
        if found_models_count == 0:
            for artist in artists_data:
                artists_models_to_create.append(create_artist_model(artist))
        else:
            # Find the data for the missing models
            for artist in artists_data:
                if not matched_artsits_models.filter(artist_link=artist['external_urls']['spotify']).exists():
                    # Creating models and adding them to list for bulk create later
                    artists_models_to_create.append(create_artist_model(artist))
        # Bulk creating models
        newly_created_models = ArtistModel.objects.bulk_create(artists_models_to_create)
        # Union of found and new models
        #matched_artsits_models.union(newly_created_models)
        matched_artsits_models = ArtistModel.objects.filter(artist_link__in=list_of_spotify_links).only('id', 'artist_link')
        return matched_artsits_models


def create_followed_models(artists_queryset, user) -> None:
    # BulkCreating followed artists models
    followed_models: list = []
    for artist in artists_queryset:
        followed_models.append(SpotifyFollowedArtistModel(
            user=user,
            artist=artist
        ))
    SpotifyFollowedArtistModel.objects.bulk_create(followed_models)

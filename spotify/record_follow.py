from requests import put
from main_page.models import ArtistModel
from profile_page.models import SpotifyFollowedArtistModel, ProfileModel
from spotify.models import SpotifyToken
from .util import is_spotify_authenticated


def record_follow(user) -> bool:
    # Check for keys expiration
    is_spotify_authenticated(user)
    # Get keys
    tokens = SpotifyToken.objects.get(user=user)
    oauth_token: str = tokens.access_token
    # Get all the followed artists models
    followed_artists_models = ArtistModel.objects.filter(SpotifyFollowedArtist__user=user)
    # Get all ids on artists into a list
    list_of_ids = get_ids_to_list(followed_artists_models)
    # Split list into section of 50
    if len(list_of_ids) > 50:
        list_of_segments: list[list[str]] = split_list(list_of_ids, 50)
    else:
        list_of_segments: list[list[str]] = [list_of_ids, ]
    # For each section make a put request
    status_check: bool = False
    for segment in list_of_segments:
        status_check = put_followed(segment, oauth_token)
    return status_check

def put_followed(ids: list[str], oauth_token: str) -> bool:
    url: str = 'https://api.spotify.com/v1/me/following'
    params: dict = {
        'type': 'artist',
        'ids': ','.join(ids)
    }
    headers: dict = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {oauth_token}"
    }

    response = put(url=url, params=params, headers=headers)
    if not response.status_code == 204:
        raise Exception(f'status code isn\'t 204\n {response.json()}')
    else:
        return True


def get_ids_to_list(artists) -> list[str]:
    list_of_ids: list[str] = []
    # Dumping all ids one by one using class methode
    for artist in artists:
        list_of_ids.append(artist.give_uri())
    return list_of_ids


def split_list(list_of_ids: list[str], segemetn_size: int) -> list[list[str]]:
    list_of_slices: list[list[str]]= []
    length = len(list_of_ids)
    slices_count: int = length // segemetn_size
    float_point: int = length % segemetn_size
    counter: int = 0
    while slices_count > counter:
        list_of_slices.append(list_of_ids[counter * segemetn_size:counter * segemetn_size + segemetn_size])
        counter += 1

    if float_point:
        list_of_slices.append(list_of_ids[slices_count * segemtn_size:length])

    return list_of_slices

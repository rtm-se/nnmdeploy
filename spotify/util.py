import requests

from .models import SpotifyToken, SpotifyProfile
from django.utils import timezone
from datetime import timedelta
from requests import post
from .credentials import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI


def get_user_tokens(user):
    user_tokens = SpotifyToken.objects.filter(user=user)
    if user_tokens.exists():
        return user_tokens[0]
    else:
        return None


def update_or_create_user_tokens(user, access_token, token_type, expires_in, refresh_token):
    tokens = get_user_tokens(user)
    expires_in = timezone.now() + timedelta(seconds=expires_in)

    if tokens:
        tokens.access_token = access_token
        tokens.refresh_token = refresh_token
        tokens.expires_in = expires_in
        tokens.token_type = token_type
        tokens.save(update_fields=['access_token', 'refresh_token', 'expires_in', 'token_type'])
    else:
        tokens = SpotifyToken(user=user, access_token=access_token, refresh_token=refresh_token,
                              expires_in=expires_in, token_type=token_type)
        tokens.save()
        create_spotify_profile_model(user, tokens)


def is_spotify_authenticated(user):
    tokens = get_user_tokens(user=user)
    if tokens:
        expiry = tokens.expires_in
        if expiry <= timezone.now():
            refresh_spotify_token(user)
        return True
    return False


def refresh_spotify_token(user):
    refresh_token = get_user_tokens(user).refresh_token

    response = post('https://accounts.spotify.com/api/token', data={
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }).json()


    access_token = response.get('access_token')
    token_type = response.get('token_type')
    refresh_token = refresh_token
    expires_in = response.get('expires_in')


    update_or_create_user_tokens(user=user, access_token=access_token, refresh_token=refresh_token,
                                    expires_in=expires_in, token_type=token_type)


def get_user_details(tokens):
    key = tokens.access_token
    headers = {'Authorization': f'Bearer    {key}'}
    params = {
        'Accept': 'application / json',
        'Content-Type': 'application/json'
    }
    link = 'https://api.spotify.com/v1/me'
    response = requests.get(link, params=params, headers=headers)

    dict_request = response.json()

    return dict_request


def create_spotify_profile_model(user, tokens):

    dict_request = get_user_details(tokens)

    display_name = dict_request['display_name']
    spotify_id = dict_request['id']
    try:
        images = dict_request['images'][0]['url']
    except:
        images = None
    external_urls = dict_request['external_urls']['spotify']
    profile = SpotifyProfile(user=user, display_name=display_name, images=images, external_urls=external_urls, spotify_id=spotify_id)
    profile.save()







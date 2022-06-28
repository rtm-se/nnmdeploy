import datetime
from threading import Thread

from requests import Request, post

from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.decorators import login_required

from .util import update_or_create_user_tokens, is_spotify_authenticated
from profile_page.models import EncounteredAlbumModel, LikeModel, RecommendationModel, SpotifyLikeModel, \
    SpotifySavedAlbumModerl
from main_page.models import ArtistModel

from .models import SpotifyToken, SpotifyProfile
from .spotify_request_script import dump_spotify_data
from .create_playlist import create_playlist
from .recommendations_requst_script import make_recommendations

from .scrap_likes import rip_likes
from .record_likes import record_likes
from .rip_albums import rip_albums
from .put_albums import put_spotify_saved_albums
from .rip_follow import record_followed_artists
from .record_follow import record_follow
from .get_recently_played_tracks import get_recent_tracks
from .get_saved_tracks import get_saved_tracks

from .credentials import REDIRECT_URI, CLIENT_ID, CLIENT_SECRET


@login_required(login_url='login:login')
def get_the_link(request):
    scopes = 'user-follow-read user-library-read user-top-read user-read-recently-played user-read-currently-playing user-read-private playlist-modify-public playlist-modify-private user-library-modify user-library-read user-follow-modify'

    url = Request('GET', 'https://accounts.spotify.com/authorize', params={
        'scope': scopes,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID
    }).prepare().url

    return redirect(url)


@login_required(login_url='login:login')
def spotify_callback(request, format=None):
    code = request.GET.get('code')
    error = request.GET.get('error')
    response = post('https://accounts.spotify.com/api/token', data={
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }).json()

    access_token = response.get('access_token')
    token_type = response.get('token_type')
    refresh_token = response.get('refresh_token')
    expires_in = response.get('expires_in')
    error = response.get('error')

    # old logging system based on session id
    # if not request.session.exists(request.session.session_key):
    #    request.session.create()

    update_or_create_user_tokens(user=request.user, access_token=access_token,
                                 token_type=token_type, expires_in=expires_in, refresh_token=refresh_token)

    return redirect('profile:connections')


@login_required(login_url='login:login')
def spotify_grab_tha_link(request):
    if not is_spotify_authenticated(user=request.user):
        return redirect('profile:connections')
    tokens = SpotifyToken.objects.get(user=request.user)

    check = dump_spotify_data(request.user, tokens.access_token)
    if check:
        # timer for test purposes
        # time.sleep(5)
        return HttpResponse('Spotify profile updated')
    else:
        pass


@login_required(login_url='login:login')
def testing_new_data_update(request):
    #get_recent_tracks(request.user)
    Thread(target=get_recent_tracks, args=(request.user, )).start()
    return HttpResponse(' <button class="btn btn-primary" type="button" disabled >Your data being updated</button>')
    #return render(request, 'spotify/get_recent_album.html')


@login_required(login_url='login:login')
def create_new_albums_playlist_view(request):
    albums = EncounteredAlbumModel.objects.filter(user=request.user, album__release_date__gte=datetime.date(2020, 1, 1))

    playlist_link = create_playlist(user=request.user, shuffle=True, albums_q=albums, page='new')

    context = {
        'playlist_link': playlist_link
    }

    return render(request, 'profile_page/list_success.html', context)


@login_required(login_url='login:login')
def create_liked_album_playlist_view(request):
    albums = LikeModel.objects.filter(user=request.user)

    playlist_link = create_playlist(user=request.user, shuffle=True, albums_q=albums, page='like')

    context = {
        'playlist_link': playlist_link
    }

    return render(request, 'profile_page/list_success.html', context)


@login_required(login_url='login:login')
def delete_spotify_data(request):
    user = request.user
    if SpotifyToken.objects.filter(user=user).exists():
        for token_data in SpotifyToken.objects.filter(user=user):
            token_data.delete()

    if SpotifyProfile.objects.filter(user=user).exists():
        for profile in SpotifyProfile.objects.filter(user=user):
            profile.delete()

    return redirect('profile:profile', pk=request.user.id)


@login_required(login_url='login:login')
def create_recommendations(request):
    albums = RecommendationModel.objects.filter(user=request.user)
    page = 'recommendation'
    if albums.exists():
        if len(albums) <= 2:
            if not make_recommendations(request.user):
                return redirect('spotify:get-auth-url')
            albums = RecommendationModel.objects.filter(user=request.user)
    else:
        albums = []
        while len(albums) < 1:
            albums = RecommendationModel.objects.filter(user=request.user)
            if not make_recommendations(request.user):
                return redirect('spotify:get-auth-url')
    context = {
        'page': page,
        'albums': albums,
        'pk': request.user.id
    }
    return render(request, 'profile_page/albums_list.html', context)


def rip_like_view(request):
    user = request.user
    total = rip_likes(user)

    if SpotifyLikeModel.objects.filter(user=user).exists():
        songs = SpotifyLikeModel.objects.filter(user=user)
    else:
        songs = 'NO LIKED SONGS'

    context = {
        'total': total,
        'songs': songs
    }
    return render(request, 'spotify/rip_likes.html', context)


def record_likes_view(request):
    user = request.user
    status = record_likes(user)
    context = {
        'status': status
    }
    return render(request, 'spotify/record_likes.html', context)


def rip_albums_view(request):
    user = request.user
    total = rip_albums(user)
    if SpotifySavedAlbumModerl.objects.filter(user=user).exists():
        albums = SpotifySavedAlbumModerl.objects.filter(user=user)
    else:
        albums = 'NO SAVED ALBUMS'

    context = {
        'albums': albums
    }
    return render(request, 'spotify/rip_albums.html', context)


def put_album_view(request):
    user = request.user

    if SpotifySavedAlbumModerl.objects.filter(user=user).exists():
        albums = SpotifySavedAlbumModerl.objects.filter(user=user)
        put_spotify_saved_albums(user=user, querry=albums)
    else:
        albums = 'NO SAVED ALBUMS'

    context = {
        'albums': albums
    }
    return render(request, 'spotify/put_albums.html', context)


@login_required(login_url='login:login')
def rip_followed_view(request):
    user = request.user
    newly_added_artists = record_followed_artists(user)
    context: dict = {
        'artists': newly_added_artists
    }
    return render(request, 'spotify/rip_followed.html', context)


@login_required(login_url='login:login')
def record_followed_view(request):
    user = request.user
    context: dict = {
        'success': True
    }
    if ArtistModel.objects.filter(SpotifyFollowedArtist__user=user).exists():
        status = record_follow(user)
        if not status:
            context.update({'success': False})

    else:
        context.update({'success': False})

    return render(request, 'spotify/record_follow.html', context=context)


@login_required(login_url='login:login')
def display_likes(request):
    user = request.user
    songs = list(SpotifyLikeModel.objects.select_related('song').filter(user=user).values_list('song__name', flat=True))
    context = {
        'items': songs
    }
    return render(request, 'spotify/saved_items.html', context)


def get_saved_songs(request):
    user = request.user
    songs = get_saved_tracks(user)
    context = {
        'songs': songs
    }
    return render(request, 'spotify/rip_likes.html', context)

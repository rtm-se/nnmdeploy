import datetime
from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.db.models import F, Value, Q, Subquery, OuterRef
from django.core.paginator import Paginator
from django.contrib.auth.models import User

from . import models
from . import forms

from spotify.playlist_creation_handler import PlaylistCreationHandler
from spotify.models import SpotifyToken, SpotifyProfile
from spotify.create_playlist import create_playlist
from main_page.models import UpcomingAlbumEntryModel, AlbumModel, SongModel
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

# Create your views here.


def profile_view(request, pk):
    user = User.objects.get(id=pk)
    profile = models.ProfileModel.objects.get(user=user)

    context = {'profile': profile}
    return render(request, 'profile_page/profile_template.html', context)


@login_required(login_url='login:login')
def connection_view(request):
    if request.method == 'POST':
        user = request.user
        SpotifyProfile.objects.get(user=user).delete()
        SpotifyToken.objects.get(user=user).delete()
        connection_status = None
        context = {'connection_status': connection_status}
        return render(request, 'profile_page/profile_connections.html', context)
    try:
        SpotifyToken.objects.filter(user=request.user)
        connection_status = True
        spotify_profile = SpotifyProfile.objects.filter(user=request.user)
        context = {'connection_status': connection_status, 'spotify_profile': spotify_profile[0]}
    except:
        connection_status = None
        context = {'connection_status': connection_status}

    return render(request, 'profile_page/profile_connections.html', context)


def listened_songs_views(request, pk):
    user = User.objects.get(id=pk)

    if request.method == 'GET' and 'page' in request.GET:
        songs = models.ListenedSongsModel.objects.select_related(
            'song'
        ).filter(user=user).order_by('-played_at').prefetch_related('song__artist')
        paginator = Paginator(songs, 30)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context = {
            'page_obj': page_obj
        }
        #raise Exception(f'{user} \n {songs} \n {page_obj}')
        return render(request, 'profile_page/song_listened_render.html', context)
    return render(request, 'profile_page/songs_listened.html')



def listened_albums_views(request, pk):
    user = User.objects.get(id=pk)
    if not user.profile.encountered_visibility and request.user != user:
        return render(request, 'profile_page/private_page.html')
    page = 'new'
    context = {
        'pk': pk,
        'page': page
    }
    return render(request, 'profile_page/albums_list.html', context)


def liked_albums_views(request, pk):
    user = User.objects.get(id=pk)
    if not user.profile.likes_visibility and request.user != user:
        return render(request, 'profile_page/private_page.html')
    albums = models.LikeModel.objects.filter(user=user, visible=True)
    page = 'like'
    context = {
        'albums': albums,
        'page': page,
        'pk': pk
    }
    return render(request, 'profile_page/albums_list.html', context)


def like_view(request, pk):
    context :dict = {}
    album = get_object_or_404(models.AlbumModel, id=pk)
    if not request.user.is_authenticated:
        context.update({
            'no_auth': True
        })
    else:
        if models.LikeModel.objects.filter(user=request.user, album=album).exists():
            likes = models.LikeModel.objects.filter(user=request.user, album=album)
            for like in likes:
                like.delete()
                is_liked = False
        else:
            like = models.LikeModel(user=request.user, album=album, visible=True)
            like.save()
            is_liked = True
        context.update({
            'is_liked': is_liked
        })

    context.update({
        'album': album
    })
    return render(request, 'like_button.html', context)


@login_required(login_url='login:login')
def old_review_update(request, pk):
    model = models.ReviewModel.objects.get(id=pk)
    if model.user != request.user:
        return redirect('main_page:album_details', pk=pk)
    if request.method == 'POST':
        form = forms.ReviewModelForm(request.POST, instance=model)
        if form.is_valid():
            form.save()
            return redirect('main_page:album_details', pk)

    form = forms.ReviewModelForm(instance=model)
    context = {
        'form': form
    }
    return render(request, 'profile_page/edit_review.html', context)


@login_required(login_url='login:login')
def old_delete_review(request, pk):
    review = models.ReviewModel.objects.get(id=pk)
    album_id = review.album.id
    if review.user != request.user:
        return redirect('main_page:album_details', pk=pk)

    if request.method == 'POST':
        review.delete()
        return redirect('main_page:album_details', album_id)

    context = {
        'review': review
    }
    return render(request, 'profile_page/delete_review.html', context)


def full_db(request):
    context = {
        'page': 'all_albums',
        'pk': 1
    }
    return render(request, 'profile_page/albums_list.html', context)


@login_required(login_url='login:login')
def visibility_view(request, page):
    if page == 'new':
        albums = models.EncounteredAlbumModel.objects.filter(
            user=request.user,
            album__release_date__gte=datetime.date(2020, 1, 1),
            album__album_type='album'
        )
    elif page == 'like':
        albums = models.LikeModel.objects.filter(
            user=request.user
        )
    context = {
        'page': page,
        'albums': albums
    }

    return render(request, 'profile_page/visibility_page.html', context)


@login_required(login_url='login:login')
def switch_visibility(request, page, pk):
    if page == 'new' or page == 'enc_que':
        querry = models.EncounteredAlbumModel.objects.get(id=pk)
    if page == 'like':
        querry = models.LikeModel.objects.get(id=pk)
    if querry.visible:
        querry.visible = False
    else:
        querry.visible = True
    querry.save()
    if page == 'enc_que':
        return encountered_que(request, pk)
    else:
        return HttpResponse('Visibility Switched')


@login_required(login_url='login:login')
def delete_page_view(request):
    return render(request, 'profile_page/delete_data.html')


def delete_all_review(request):
    user = request.user
    if models.ReviewModel.objects.filter(user=user).exists():
        reviews = models.ReviewModel.objects.filter(user=user)
        for review in reviews:
            review.delete()

    return redirect('profile:profile', pk=request.user.id)


def delete_all_songs_album(request):
    user = request.user
    if models.EncounteredAlbumModel.objects.filter(user=user).exists():
        albums_listened = models.EncounteredAlbumModel.objects.filter(user=user)
        for album in albums_listened:
            album.delete()

    if models.ListenedSongsModel.objects.filter(user=user).exists():
        songs = models.ListenedSongsModel.objects.filter(user=user)
        for song in songs:
            song.delete()

    return redirect('profile:profile', pk=request.user.id)


def delete_all_likes(request):
    user = request.user
    if models.LikeModel.objects.filter(user=user).exists():
        likes = models.LikeModel.objects.filter(user=user)
        for like in likes:
            like.delete()

    return redirect('profile:profile', pk=request.user.id)


def all_reviews_view(request, pk):
    user = User.objects.get(id=pk)
    if not user.profile.reviews_visibility and request.user != user:
        return render(request, 'profile_page/private_page.html')
    if models.ReviewModel.objects.filter(user=user).exists():
        reviews = models.ReviewModel.objects.filter(user=user)
    else:
        reviews = None

    context = {
        'reviews': reviews
    }

    return render(request, 'profile_page/all_reviews.html', context)


def add_to_wl_view(request, pk):
    if not request.user.is_authenticated:
        return HttpResponse(f'please log in')
    user = request.user
    upcoming_album = UpcomingAlbumEntryModel.objects.get(id=pk)
    if models.WaitingListAlbumModel.objects.filter(user=user, upcoming_album=upcoming_album).exists():
        waiting_obj = models.WaitingListAlbumModel.objects.filter(user=user, upcoming_album=upcoming_album)
        for obj in waiting_obj:
            obj.delete()
    else:
        waiting_obj = models.WaitingListAlbumModel(user=user, upcoming_album=upcoming_album)
        waiting_obj.save()

    waiting_index = models.WaitingListAlbumModel.objects.filter(upcoming_album=upcoming_album).count()
    return HttpResponse(f'{waiting_index}')


def waiting_list_view(request, pk):
    user = User.objects.get(id=pk)
    date_check = datetime.date.today()
    upcoming_list = models.WaitingListAlbumModel.objects.filter(user=user, upcoming_album__release_date__gt=date_check)
    released_list = models.WaitingListAlbumModel.objects.select_related(
        'upcoming_album', 'upcoming_album__album'
    ).filter(
        user=user, upcoming_album__release_date__lte=date_check
    )  # .exclude(user__encountered_album__album=)

    context = {
        'user': user,
        'upcoming_list': upcoming_list,
        'released_list': released_list
    }
    return render(request, 'profile_page/waiting_list.html', context)


def fav_album_view(request):
    if not request.user.is_authenticated:
        return HttpResponse(f'please log in')
    user = request.user
    albums = models.LikeModel.objects.filter(user=user)

    context = {
        'albums': albums
    }
    return render(request, 'profile_page/fav_album.html', context)


@login_required(login_url='login:login')
def place_fave_album(request, pk):
    user = request.user
    profile = models.ProfileModel.objects.get(user=user)
    profile.favorite_album = AlbumModel.objects.get(id=pk)
    profile.save()
    return redirect('profile:profile', request.user.id)


@login_required(login_url='login:login')
def old_encountered_que(request):
    user = request.user
    form = forms.ReviewModelForm()

    if request.method == 'POST':
        encountered_model_id = int(request.POST['next'])

        encountered_models = models.EncounteredAlbumModel.objects.filter(
            user=user,
            album__release_date__gte=datetime.date(2020, 1, 1),
            id__gt=encountered_model_id,
            album__album_type='album'
        )
        if not encountered_models.exists():
            return redirect('profile:profile', user.id)
        album_count = encountered_models.count()

        songs = set(
            models.ListenedSongsModel.objects.filter(user=user, song__album=encountered_models[0].album).values_list(
                'song__name'))
        songs = [str(song)[2:-3] for song in songs]

        context = {
            'encountered_model': encountered_models[0],
            'percentage': encountered_models[0].completion,
            'album_count': album_count,
            'songs': songs,
            'form': form

        }
    else:
        encountered_models = models.EncounteredAlbumModel.objects.filter(
            user=user,
            album__release_date__gte=datetime.date(2020, 1, 1),
            album__album_type='album'
        )
        if encountered_models.exists():
            album_count = encountered_models.count()
        else:
            # todo make an error page for when you don't have encountered albums
            return redirect('main_page:home')

        songs = set(
            models.ListenedSongsModel.objects.filter(user=user, song__album=encountered_models[0].album).values_list(
                'song__name'))
        songs = [str(song)[2:-3] for song in songs]
        print(songs)
        context = {
            'encountered_model': encountered_models[0],
            'percentage': encountered_models[0].completion,
            'album_count': album_count,
            'songs': songs,
            'form': form
        }
    return render(request, 'profile_page/encountered_que.html', context)


# make a seperate function that will help with getting infor and will make an object with links to data
def get_info_on_the_album():
    pass


@login_required(login_url='login:login')
def edit_profile_view(request):
    user = request.user
    profile_instance = models.ProfileModel.objects.filter(user=user)[0]
    if request.method == 'POST':
        form = forms.UserProfileForm(request.POST, request.FILES, instance=profile_instance)
        if form.is_valid():
            form.save()

            return redirect('profile:profile', user.id)

    form = forms.UserProfileForm(instance=profile_instance)
    context = {
        'form': form
    }
    return render(request, 'profile_page/edit_profile.html', context)


@login_required(login_url='login:login')
def review_update(request, pk):
    user = request.user
    review = models.ReviewModel.objects.get(id=pk)
    if review.user != user:
        return HttpResponse('WRONG USER')
    if request.method == 'GET':
        form = forms.ReviewModelForm(instance=review)
        page = 'EDIT'
        context = {
            'album_id': review.album.id,
            'review_id': review.id,
            'form': form,
            'page': page
        }
        return render(request, 'profile_page/update_review_card.html', context)
    if request.method == 'POST':
        form = forms.ReviewModelForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            page = 'REVIEW'
            context = {
                'page': page,
                'review': review
            }

            return render(request, 'profile_page/update_review_card.html', context)
        else:
            return HttpResponse('AN ERROR OCCURRED DURING FORM VALIDATION')


@login_required(login_url='login:login')
def cancel_review_update(request, pk):
    user = request.user
    review = models.ReviewModel.objects.get(id=pk)
    if review.user != user:
        return HttpResponse('WRONG USER')
    if request.method == 'POST':
        page = 'REVIEW'
        form = forms.ReviewModelForm()
        context = {
            'review': review,
            'page': page
        }
        return render(request, 'profile_page/update_review_card.html', context)


@login_required(login_url='login:login')
def delete_review(request, pk):
    user = request.user
    review = models.ReviewModel.objects.get(id=pk)
    if review.user != user:
        return HttpResponse('WRONG USER')
    if request.method == 'POST':
        album_id = review.album.id
        review.delete()
        page = 'EMPTY'
        form = forms.ReviewModelForm()
        context = {
            'album_id': album_id,
            'form': form,
            'page': page
        }
        return render(request, 'profile_page/update_review_card.html', context)


@login_required(login_url='login:login')
def post_review(request, pk):
    user = request.user
    if request.method == 'POST':
        form = forms.ReviewModelForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = user
            album = AlbumModel.objects.get(id=pk)
            review.album = album
            review.save()
            page = 'REVIEW'
            context = {
                'page': page,
                'review': review
            }

            return render(request, 'profile_page/update_review_card.html', context)
        else:
            return HttpResponse('AN ERROR OCCURRED DURING FORM VALIDATION')


@login_required(login_url='login:login')
def profile_playlist_view(request):
    user = request.user
    albums = models.ProfileModel.objects.get(user=user).playlist_albums.all()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login:login')
        page = 'playlist'

        playlist_link = create_playlist(user=request.user, albums_q=albums, shuffle=request.POST.get('shuffle'),
                                        page=page)
        context = {
            'playlist_link': playlist_link
        }
        if request.POST.get('wipe') == 'on':
            models.ProfileModel.objects.get(user=user).playlist_albums.clear()
        return render(request, 'profile_page/list_success.html', context)

    context = {
        'albums': albums
    }
    return render(request, 'profile_page/playlist_list.html', context)


@login_required(login_url='login:login')
def add_to_playlist(request, pk):
    user = request.user
    album = AlbumModel.objects.get(id=pk)
    profile = models.ProfileModel.objects.get(user=user)
    if album in profile.playlist_albums.all():
        pass
    else:
        profile.playlist_albums.add(album)
        profile.save()
    return render(request, 'profile_page/added_playlist_buttons.html')


@login_required(login_url='login:login')
def delete_playlist_item(request, pk):
    user = request.user
    album = AlbumModel.objects.get(id=pk)
    user.profile.playlist_albums.remove(album)
    return HttpResponse('')


@login_required(login_url='login:login')
def delete_recommendation_item(request, pk):
    user = request.user
    album = models.RecommendationModel.objects.get(user=user, album__id=pk)
    album.delete()
    return HttpResponse('')


@login_required(login_url='login:login')
def delete_data_view(request):
    if request.method == 'POST':
        user = request.user
        deletion_choices_keys = request.POST.keys()

        if 'reviews' in deletion_choices_keys:
            reviews = models.ReviewModel.objects.filter(user=user)
            if reviews.exists():
                for review in reviews:
                    review.delete()

        if 'spotifyprofile' in deletion_choices_keys:
            spotify_profile = SpotifyProfile.objects.filter(user=user)
            if spotify_profile.exists():
                for profile in spotify_profile:
                    profile.delete()

            tokens_profile = SpotifyToken.objects.filter(user=user)
            if tokens_profile.exists():
                for token in tokens_profile:
                    token.delete()

        if 'likedalbums' in deletion_choices_keys:
            likes = models.LikeModel.objects.filter(user=user)
            if likes.exists():
                for like in likes:
                    like.delete()
            models.ProfileModel.objects.filter(user=user).update(favorite_album=None)

        if 'listenedalbumssongs' in deletion_choices_keys:
            encountered = models.EncounteredAlbumModel.objects.filter(user=user)
            if encountered.exists():
                for album in encountered:
                    album.delete()

            encountered_songs = models.ListenedSongsModel.objects.filter(user=user)
            if encountered_songs.exists():
                for song in encountered_songs:
                    song.delete()

        if 'savedalbums' in deletion_choices_keys:
            saved_albums = models.SpotifySavedAlbumModerl.objects.filter(user=user)
            if saved_albums.exists():
                for album in saved_albums:
                    album.delete()

        if 'savedsongs' in deletion_choices_keys:
            saved_songs = models.ListenedSongsModel.objects.filter(user=user)
            if saved_songs.exists():
                for song in saved_songs:
                    song.delete()

        return HttpResponse('Data Deleted')


@login_required(login_url='login:login')
def live_search_visibility(request, page):
    if request.method == 'POST':
        user = request.user
        q = request.POST.get('search')
        if page == 'new':
            albums = models.EncounteredAlbumModel.objects.filter(user=user, album__name__icontains=q)
        elif page == 'like':
            albums = models.LikeModel.objects.filter(user=user, album__name__icontains=q)
        context = {
            'page': page,
            'albums': albums
        }
        return render(request, 'profile_page/visibilit_page_abulms.html', context)


@login_required(login_url='login:login')
def no_review_section(request, pk):
    user = request.user
    albums = models.EncounteredAlbumModel.objects.filter(
        user=user,
        id__gt=pk, completion=100,
        album__album_type='album',
        album__release_date__gte=datetime.date(2020, 1, 1)).order_by('id').exclude(
        album__review__user=user)
    try:
        context = {
            'album': albums[0],
            'page': 'no_review'
        }
    except:
        if request.method == 'POST':
            context = {
                'page': 'END_QUE'
            }
            return render(request, 'profile_page/que_albums_album_component.html', context)
        else:
            return render(request, 'profile_page/end_que.html')
    if request.method == 'POST':
        return render(request, 'profile_page/que_albums_album_component.html', context)
    else:

        return render(request, 'profile_page/que_albums.html', context)


@login_required(login_url='login:login')
def give_form_for_a_review(request, pk):
    form = forms.ReviewModelForm()
    page = 'EMPTY'
    context = {
        'album_id': pk,
        'form': form,
        'page': page,
        'button': True
    }
    return render(request, 'profile_page/update_review_card.html', context)


@login_required(login_url='login:login')
def encountered_que(request, pk):
    user = request.user
    albums = models.EncounteredAlbumModel.objects.filter(
        user=user,
        id__gt=pk, completion__lt=100,
        album__album_type='album',
        visible=True,
        album__release_date__gte=datetime.date(2020, 1, 1)).order_by('id')
    if albums.exists():
        if albums[0].album in user.profile.playlist_albums.all():
            album_playlist_check = True
        else:
            album_playlist_check = False
        likes_models = models.LikeModel.objects.filter(album=albums[0].album, user=user)
        if likes_models.exists():
            likes = likes_models.count()
            like = True
        else:
            likes = 0
            like = False
    try:
        context = {
            'album': albums[0],
            'like': like,
            'likes': likes,
            'album_playlist_check': album_playlist_check,
            'page': 'encounter'
        }
    except:
        if request.method == 'POST':
            context = {
                'page': 'END_QUE'
            }
            return render(request, 'profile_page/que_albums_album_component.html', context)
        else:
            return render(request, 'profile_page/end_que.html')
    if request.method == 'POST':
        return render(request, 'profile_page/que_albums_album_component.html', context)
    else:

        return render(request, 'profile_page/que_albums.html', context)


@login_required(login_url='login:login')
def get_enc_album_info(request, pk):
    if pk == 0:
        return HttpResponse('<div id="album_mobile_details"></div>')
    album = models.EncounteredAlbumModel.objects.get(id=pk)
    context = {
        'album': album
    }
    return render(request, 'profile_page/album_click_details.html', context)


def render_like(request, pk):
    if not request.user.is_authenticated:
        is_liked = False
    else:
        user = request.user
        if models.LikeModel.objects.filter(user=user, album__id=pk).exists():
            is_liked = True
        else:
            is_liked = False
    album = AlbumModel.objects.get(id=pk)
    context = {
        'album': album,
        'is_liked': is_liked
    }
    return render(request, 'like_button.html', context)


def show_albums_list(request, page, pk):
    user = User.objects.get(id=pk)
    if page == 'new':

        albums = AlbumModel.objects.prefetch_related('artist_name').filter(
            encountered_user__user=user,
            release_date__gte=datetime.date(2020, 1, 1),
            encountered_user__visible=True,
            album_type='album',
        )
        paginator = Paginator(albums, 12)
        if request.method == 'GET' and 'page_n' in request.GET:
            page_number = request.GET.get('page_n')
            page_obj = paginator.page(page_number)
            context = {
                'page_obj': page_obj
            }
            return render(request, 'profile_page/test_albums.html', context)
        # albums = models.EncounteredAlbumModel.objects.select_related('album').prefetch_related('album__artist_name').filter(
        #     user=user,
        #     album__release_date__gte=datetime.date(2020, 1, 1),
        #     album__album_type='album',
        #     visible=True
        # ).order_by('-completion')
        # Checking for owner of the list and updating completion
        if user == request.user:
            for album in albums:
                album.get_song_completion()

        if request.GET.get('select_value') == '100' or request.POST.get('select_value') == '100':

            albums = albums.exclude(completion__lt=100)
        if request.GET.get('select_value') == '99' or request.POST.get('select_value') == '99':

            albums = albums.exclude(completion=100)
    elif page == 'like':
        albums = models.LikeModel.objects.filter(user=user, visible=True)
    elif page == 'recommendation':
        albums = models.RecommendationModel.objects.filter(user=user)
    else:
        albums = models.EncounteredAlbumModel.objects.filter(album__release_date__gte=datetime.date(2020, 1, 1),
                                                             album__album_type='album')

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login:login')
        playlist_creator = PlaylistCreationHandler(
            user=request.user,
            albums=albums,
            shuffle_check=request.POST.get('shuffle'),
            page=page
        )
        playlist_link = playlist_creator.playlist_link
        context = {
            'playlist_link': playlist_link
        }
        return render(request, 'profile_page/list_success.html', context)


    context = {
        'pk': pk,
        'page': page,
        'albums': albums
    }
    return render(request, 'profile_page/albums_list_list.html', context)


@login_required(login_url='login:login')
def make_playlist(request, page, albums):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login:login')
        playlist_link = create_playlist(user=request.user, albums_q=albums, shuffle=request.POST.get('shuffle'),
                                        page=page)
        context = {
            'playlist_link': playlist_link
        }
        return render(request, 'profile_page/list_success.html', context)



def del_wl_item(request, pk):
    if not request.user.is_authenticated:
        return HttpResponse('Please Log In')
    try:
        item = models.WaitingListAlbumModel.objects.get(id=pk)
        if item.user == request.user:
            item.delete()
            return HttpResponse('Deleted')
        else:
            return HttpResponse('Wrong user')
    except:
        return HttpResponse('wrong response')


@login_required(login_url='login:login')
def delete_review_from_many(request, pk):
    user = request.user
    review = models.ReviewModel.objects.get(id=pk)
    if review.user == user:
        review.delete()
        return HttpResponse('Deleted')
    else:
        return HttpResponse('Wrong User')



def delete_profile_data(request):
    if request.method == 'POST':

        user = request.user
        logout(request)
        user.delete()

        context = {
            'page': 'post_delete'
        }
    else:
        context = {
            'page': 'confirmation'
        }
    return render(request, 'profile_page/delete_profile.html', context)


def albums_view(request, page, pk):
    # Function view responsible for render of albums lists on likes and encountered pages
    # Getting user object to search for albums and check permissions
    print(page)
    try:
        user = User.objects.get(id=pk)
    except:
        # TODO add more strict exception claws and show this page only if you can't find a user
        return render(request, 'profile_page/private_page.html')
    # Checking visibility of the page

    visibility: bool = bool()
    if page == 'albums_listened':
        visibility = user.profile.encountered_visibility
    elif page == 'albums_liked':
        visibility = user.profile.likes_visibility
    if not visibility and user != request.user:
        return render(request, 'profile_page/private_page.html')

    # Rendering the base page if there's no pagintor's n of page
    if not 'page_n' in request.GET:
        context = {
            'pk': pk,
            'page': page
        }
        return render(request, 'profile_page/albums_list.html', context)
    else:
        print(request.GET)
        context: dict = dict()
        if page == 'albums_listened':
            albums = AlbumModel.objects.prefetch_related('artist_name').filter(
                encountered_user__user=user,
                release_date__gte=datetime.date(2020, 1, 1),
                album_type='album',
                encountered_user__visible=True).distinct().annotate(completion=Subquery(
                models.EncounteredAlbumModel.objects.filter(
                album__id=OuterRef('id'),
                user=user
                ).values('completion')
            )).order_by('-completion')
            if 'select_value' in request.GET:
                if request.GET.get('select_value') == '100' or request.POST.get('select_value') == '100':
                    albums = albums.exclude(completion__lt=100)
                elif request.GET.get('select_value') == '99' or request.POST.get('select_value') == '99':
                    albums = albums.exclude(completion=100)

                context.update({'select_value': request.GET.get('select_value')})
        if page == 'albums_liked':
            albums = AlbumModel.objects.filter(
                album_type='album',
                like__user=user,
                like__visible=True)
        paginator = Paginator(albums, 12)
        page_n = request.GET.get('page_n')
        page_obj = paginator.page(page_n)
        context.update({
            'page_obj': page_obj,
            'page': page
        })
        return render(request, 'profile_page/test_albums.html', context)


#CompetitionTeam.objects.filter(competition_id=_competition.id,team_id__in=joined_team_ids).annotate(name=Subquery(Team.objects.filter(id=OuterRef('team_id')).values('name')))


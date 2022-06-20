import datetime
from django.db.models import Q
from django.shortcuts import render, redirect, reverse
from django.contrib.auth.models import User
from django.contrib import messages
from . import models
from profile_page.forms import ReviewModelForm
from profile_page.models import LikeModel, ReviewModel, WaitingListAlbumModel, EncounteredAlbumModel, ListenedSongsModel


# Create your views here.


def upcoming_new_main_view(request):
    # check if it's friday to make script look for mathes on released - unreleased albums
    date_check = datetime.date.today()
    if date_check.weekday() == 4:
        upcoming_albums_today = models.UpcomingAlbumEntryModel.objects.filter(release_date=date_check)
        for album in upcoming_albums_today:
            if album.album is None:
                album.match_release()
    else:
        upcoming_albums_today = None
    upcoming_albums = models.UpcomingAlbumEntryModel.objects.filter(release_date__gt=date_check)[:10]
    new_albums = models.AlbumModel.objects.filter(release_date__gte=datetime.date(2020, 1, 1), album_type='album')[:10]
    context = {
        'upcoming_albums': upcoming_albums,
        'new_albums': new_albums,
        'upcoming_albums_today': upcoming_albums_today,
    }
    return render(request, 'main_page/main_page.html', context)


'''
class CalendarListView(ListView):
    model = models.UpcomingAlbumEntryModel
    template_name = 'main_page/main_page.html'
    context_object_name = 'album_list'
'''


def upcoming_detail_view(request, pk):
    album = models.UpcomingAlbumEntryModel.objects.get(id=pk)
    artists = album.artist_name.all()
    upcoming_index = WaitingListAlbumModel.objects.filter(upcoming_album__id=pk).count()

    context = {
        'album': album,
        'artists': artists,
        'upcoming_index': upcoming_index
    }
    return render(request, 'main_page/upcoming_details.html', context)


def old_album_details(request, pk):
    album = models.AlbumModel.objects.get(id=pk)
    if request.method == 'POST':
        if ReviewModel.objects.filter(user=request.user, album=album).exists():
            return redirect('main_page:album_details', pk=pk)
        form = ReviewModelForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.album = album
            review.save()
            return redirect(reverse('main_page:album_details', args=[pk]))
        else:
            messages.error(request, 'Wrong submmition')
    if request.user.is_authenticated:
        if EncounteredAlbumModel.objects.filter(user=request.user, album=album).exists():
            completion = EncounteredAlbumModel.objects.filter(user=request.user, album=album)[0].completion
            if completion > 39:
                form = ReviewModelForm()
            else:
                form = False
        else:
            form = False
    likes = len(LikeModel.objects.filter(album__id=pk))
    reviews = ReviewModel.objects.filter(album__id=pk)
    # todo add rating functionality with sorting according to the rating
    context = {'album': album, 'likes': likes, 'reviews': reviews}

    if request.user.is_authenticated:
        if not ReviewModel.objects.filter(album__id=pk, user=request.user).exists():
            context.update({'form': form})

    return render(request, 'main_page/album_details.html', context)


def search_bar_view(request):
    if request.method == 'GET':
        q = request.GET.get('q')
        date_check = datetime.date.today()
        # no possibility to use Q() and format the final page
        search_albums = models.AlbumModel.objects.filter(name__icontains=q)
        artists = models.AlbumModel.objects.filter(artist_name__name__icontains=q)
        users = User.objects.filter(username__icontains=q)
        #possible to cheat the sustem with Q
        upcoming = models.UpcomingAlbumEntryModel.objects.filter(Q(release_date__gt=date_check, album_name__icontains=q) | Q(release_date__gt=date_check, artist_name__name__icontains=q))

        context = {
            'albums': search_albums[0:10],
            'artists': artists[0:10],
            'users': users[0:10],
            'upcoming': upcoming[0:10],
            'q': q
        }
    else:
        return redirect('main_page:home')
    return render(request, 'main_page/search_page.html', context)


def search_albums(request, q):
    albums = models.AlbumModel.objects.filter(name__icontains=q)
    context = {
        'context_list': albums,
        'search_name': 'Albums'
    }
    return render(request, 'main_page/search_albums.html', context)


def search_artists(request, q):
    artists = models.AlbumModel.objects.filter(artist_name__name__icontains=q)
    context = {
        'context_list': artists,
        'search_name': 'Artists'
    }
    return render(request, 'main_page/search_albums.html', context)


def search_users(request, q):
    users = User.objects.filter(username__icontains=q)
    context = {
        'context_list': users,
        'search_name': 'Users'
    }
    return render(request, 'main_page/search_albums.html', context)


def search_upcoming(request, q):
    date_check = datetime.date.today()
    upcoming = models.UpcomingAlbumEntryModel.objects.filter(Q(release_date__gt=date_check, album_name__icontains=q) | Q(release_date__gt=date_check, artist_name__name__icontains=q))
    context = {
        'context_list': upcoming,
        'search_name': 'Upcoming'
    }
    return render(request, 'main_page/search_albums.html', context)


def album_details(request, pk):
    user = request.user
    album = models.AlbumModel.objects.get(id=pk)
    page = 'album_detail'
    likes = LikeModel.objects.filter(album=album).count()
    if request.user.is_authenticated:
        reviews = ReviewModel.objects.filter(album=album,  user__profile__reviews_visibility=True).exclude(user=user)

        if album in user.profile.playlist_albums.all():
            album_playlist_check = True
        else:
            album_playlist_check = False
        # checking if user wrote a review
        if ReviewModel.objects.filter(album=album, user=user).exists():
            user_review = ReviewModel.objects.get(album=album, user=user)
            form = None
        else:
            user_review = None
            form = ReviewModelForm()

        # checkign for songs listened
        if EncounteredAlbumModel.objects.filter(user=user, album=album).exists():
            encountered_instance = EncounteredAlbumModel.objects.get(user=user, album=album)

            songs = set(ListenedSongsModel.objects.filter(user=user, song__album=album).values_list('song__name', flat=True))

        else:
            encountered_instance = None
            songs = None
    else:
        reviews = ReviewModel.objects.filter(album=album, user__profile__reviews_visibility=True)
        encountered_instance = None
        songs = None
        user_review = None
        form = None
        album_playlist_check = False
    context = {
        'album_playlist_check': album_playlist_check,
        'album': album,
        'reviews': reviews,
        'page': page,
        'encountered_instance': encountered_instance,
        'songs': songs,
        'form': form,
        'likes': likes,
        'user_review': user_review
    }
    return render(request, 'main_page/album_detail.html', context)

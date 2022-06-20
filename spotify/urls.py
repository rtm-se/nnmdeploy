from django.urls import path
from . import views

app_name = 'spotify'

urlpatterns = [
    path('get-auth-url/', views.get_the_link, name='get-auth-url'),
    path('redirect/', views.spotify_callback, name='redirect'),
    #path('is-authenticated/', views.IsAuthenticated.as_view(), name='is-authenticated'),
    path('grab_the_link/', views.spotify_grab_tha_link, name='grab_tha_link'),
    path('playlist/new/', views.create_new_albums_playlist_view, name='create_new_playlist'),
    path('playlist/liked/', views.create_liked_album_playlist_view, name='create_liked_playlist'),
    path('delete_spotify_data/', views.delete_spotify_data, name='delete_data'),
    path('make_recommendations/', views.create_recommendations, name='recommendations'),
    path('rip_likes/', views.rip_like_view, name='rip_likes'),
    path('rip_albums/', views.rip_albums_view, name='rip_albums'),
    path('record_likes/', views.record_likes_view, name='record_likes'),
    path('put_albums/', views.put_album_view, name='put_albums'),
    path('rip_followed/', views.rip_followed_view, name='rip_followed'),
    path('record_followed_view/', views.record_followed_view, name='record_followed_view'),
    path('new_data/', views.testing_new_data_update, name='test_data_update'),
    path('display_likes/', views.display_likes, name='display_likes'),
    path('get_saved_songs/', views.get_saved_songs, name='get_saved_songs')

]


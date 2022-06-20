from django.urls import path
from . import views
app_name = 'profile'

urlpatterns = [
    path('<int:pk>/', views.profile_view, name='profile'),
    path('connections/', views.connection_view, name='connections'),
    #todo come up with the less obvious link
    path('songs_listened/<int:pk>/', views.listened_songs_views, name='songs_listened'),
    path('albums_listened/<int:pk>', views.listened_albums_views, name='albums_listened'),
    path('albums_liked/<int:pk>', views.liked_albums_views, name='albums_liked'),
    path('all_new_albums/', views.full_db, name='full_db'),
    path('post_review/<int:pk>', views.post_review, name='post_review'),
    path('update_review/<int:pk>', views.review_update, name='edit_review'),
    path('delete_review/<int:pk>', views.delete_review, name='delete_review'),
    path('visibility/<str:page>', views.visibility_view, name='visibility'),
    path('visibility/<str:page>/switch_visibility/<int:pk>', views.switch_visibility, name='switch_visibility'),
    path('delete_Info/', views.delete_page_view, name='delete_page'),
    path('all_reviews/<int:pk>', views.all_reviews_view, name='all_reviews'),
    path('wl/<int:pk>/', views.waiting_list_view, name='wl'),
    path('fav_album/', views.fav_album_view, name='fav_album'),
    path('make_fave/<int:pk>/', views.place_fave_album, name='make_fav'),
    path('encountred_que/<int:pk>', views.encountered_que, name='encountered_que'),
    path('edit_profile/', views.edit_profile_view, name='edit_profile'),
    path('cancel_review_update/<int:pk>/', views.cancel_review_update, name='cancel_review_update'),
    path('give_form_for_a_review/<int:pk>', views.give_form_for_a_review, name='give_form_for_a_review'),
    path('add_to_playlist/<int:pk>', views.add_to_playlist, name='add_to_playlist'),
    path('playlist/', views.profile_playlist_view, name='playlist'),
    path('delete_playlist_item/<int:pk>', views.delete_playlist_item, name='delete_playlist_item'),
    path('delete_recommendation_item/<int:pk>', views.delete_recommendation_item, name='delete_recommendation_item'),
    path('delete_data_view/', views.delete_data_view, name='delete_data_view'),
    path('live_search_visibility/<str:page>/', views.live_search_visibility, name='live_search_visibility'),
    path('no_review_section/<int:pk>', views.no_review_section, name='no_review_section'),
    path('get_enc_album_info/<int:pk>/', views.get_enc_album_info, name='get_enc_album_info'),
    path('render_like/<int:pk>/', views.render_like, name='render_like'),
    path('show_albums_list/<str:page>/<int:pk>/', views.show_albums_list, name='show_albums_list'),
    path('del_wl_item/<int:pk>', views.del_wl_item, name='del_wl_item'),
    path('delete_review_from_many/<int:pk>', views.delete_review_from_many, name='delete_review_from_many'),
    path('delete_profile', views.delete_profile_data, name='delete_profile')

]
from django.urls import path
from . import views
from profile_page.views import like_view, add_to_wl_view
app_name = 'main_page'


urlpatterns = [
    #path('', views.CalendarListView.as_view(), name='home'),
    path('', views.upcoming_new_main_view, name='home'),
    path('upcoming/<int:pk>/', views.upcoming_detail_view, name='upcoming_details'),
    path('upcoming/<int:pk>/add_wl/', add_to_wl_view, name='add_wl'),
    path('AlbumDetails/<int:pk>/', views.album_details, name='album_details'),
    path('AlbumDetails/<int:pk>/like_post/', like_view, name='like_post'),
    path('search/', views.search_bar_view, name='search'),
    path('search_albums/<str:q>', views.search_albums, name='search_albums'),
    path('search_artists/<str:q>', views.search_artists, name='search_artists'),
    path('search_users/<str:q>', views.search_users, name='search_users'),
    path('search_upcoming/<str:q>', views.search_upcoming, name='search_upcoming'),


    #path('', MainPageTemplateView.as_view(), name='home')
]

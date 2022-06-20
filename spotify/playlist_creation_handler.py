from random import choices, shuffle
import requests
from django.shortcuts import redirect
from .models import SpotifyToken, SpotifyProfile
from main_page.models import AlbumModel
from spotify.util import is_spotify_authenticated


class PlaylistCreationHandler:
    '''
    be sure to pass albums with .link .album_songs_sting and .id preloaded
    '''

    def __init__(self, user, albums, page, shuffle_check):
        self.albums = albums
        self.album_ids = None
        self.page = page
        self.user = user
        self.shuffle_check = shuffle_check

        # for updating albums data base
        self.unfilled_albums = []
        self.albums_to_update = []

        if is_spotify_authenticated(self.user):
            self.get_spotify_profile_data()
        else:
            return redirect('spotify:get-auth-url')
        print('getting albums from querry')
        self.get_albums_querry_from_set()
    #check for empty link albums
        print('checking albums for empty stings')
        self.check_for_empty_songs_string()
    #dump strings
        print('dumping ids of songs')
        song_ids_split = self.dump_song_ids()
        print(song_ids_split[-1])
        print(song_ids_split[-2])
    #get new playlist
        print('creating new list')
        self.get_new_playlist_link()
        #check for shuffle
        if self.shuffle_check:
            print('shuffle')
            shuffle(song_ids_split)
            if len(song_ids_split) > 30:
                song_ids_split = song_ids_split[:29]
                self.add_song_to_playlist(song_ids_split)
            else:
                self.add_song_to_playlist(song_ids_split)
        else:
            print('non_suffle')
            if len(song_ids_split) > 50:

                song_ids_split = self.split_list(50, song_ids_split)
                for segment in song_ids_split:
                    self.add_song_to_playlist(segment)
            else:
                self.add_song_to_playlist(song_ids_split)


    def get_albums_querry_from_set(self):
        #reducing the data to just the albums
        if self.album_ids is None:
            self.album_ids = [alb_id for alb_id in self.albums.values_list('album__id', flat=True)]
            self.albums = AlbumModel.objects.filter(id__in=self.album_ids).only('id', 'link', 'album_songs_sting')
        else:
            self.albums = AlbumModel.objects.filter(id__in=self.album_ids).only('id', 'album_songs_sting')
        #populating cache
        [album for album in self.albums]
        return True


    def get_spotify_profile_data(self):
        self.spotify_profile = SpotifyProfile.objects.get(user=self.user)
        self.spotify_id = self.spotify_profile.spotify_id

        self.spotify_token = SpotifyToken.objects.get(user=self.user)
        self.access_token = self.spotify_token.access_token


    def get_new_playlist_link(self):
        link = f'https://api.spotify.com/v1/users/{self.spotify_id}/playlists'
        if self.page == 'like':
            name = "NoNM's likes playlist "
        elif self.page == 'new':
            name = "NoNM's new albums playlist "
        elif self.page == 'playlist':
            name = f"NoNW's {self.user.username} playlist"
        else:
            name = "NoNM's playlist"
        body = {
            "name": name,
            "description": "New playlist description",
            "public": False
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }
        response = requests.post(link, json=body, headers=headers)

        data_dict = response.json()
        self.playlist_id = data_dict['id']
        self.playlist_link = "https://open.spotify.com/playlist/" + self.playlist_id

        return True

    def unfilled_albums_check(self):
        self.unfilled_albums = self.albums.filter(album_songs_sting=None).only('album_songs_sting', 'link')

        if self.unfilled_albums.exists():
            return True
        else:
            return False

    def add_song_to_playlist(self, song_ids):
        print('starting adding songs from request')
        link = f'https://api.spotify.com/v1/playlists/{self.playlist_id}/tracks'

        data = {
            'uris': 'spotify:track:' + ',spotify:track:'.join(song_ids)
        }
        print(data)

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }

        response = requests.post(link, params=data, headers=headers)
        if response.status_code == 200:
            print(response.status_code)
            print(response.json())
            return True
        else:
            print(response.status_code)
            print(response.json())
            return False


    def split_list(self, segment_size, ids_list):
        sections_count = len(ids_list) // segment_size
        remains = ids_list[sections_count * segment_size:]
        ids_list = [ids_list[segment_size * section: segment_size * section + segment_size] for section in
                    range(sections_count)]
        ids_list.append(remains)

        return ids_list

    def get_albums_info(self, ids):
        link = f"https://api.spotify.com/v1/albums/"
        params = {
            'ids': ','.join(ids),
            "market": 'US'
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            'Authorization': f'Bearer {self.access_token}'
        }

        response = requests.get(link, params=params, headers=headers)
        if response.status_code != 200:
            print('ERROR OCCURED DURING REQUEST')
            print(response.status_code)
            print(response.json())
            print(response.headers)
            return False
        data_dict = response.json()
        albums = data_dict['albums']
        updated_albums = []
        for album in albums:
            working_album = self.unfilled_albums.get(link=album['external_urls']['spotify'])
            print(working_album)
            songs_ids = []
            for song in album['tracks']['items']:
                songs_ids.append(song['id'])
            print(songs_ids)

            working_album.album_songs_sting = ','.join(songs_ids)
            #todo bulk update working albums
            updated_albums.append(working_album)

        AlbumModel.objects.bulk_update(updated_albums, ['album_songs_sting'])

        return True

    def check_for_empty_songs_string(self):
        albums_id_empty_strings = []

        if self.unfilled_albums_check():
            for album in self.unfilled_albums:
                albums_id_empty_strings.append(album.uri())
                # checking if there are albums to update
            albums_id_empty_strings = list(set(albums_id_empty_strings))

                # checking if the sting for albums would be too long to update in one time
            if len(albums_id_empty_strings) > 20:
                for splitted_section in self.split_list(20, albums_id_empty_strings):
                    self.get_albums_info(splitted_section)

            else:
                self.get_albums_info(albums_id_empty_strings)

            self.get_albums_querry_from_set()
            #print('updating albums')
            #AlbumModel.objects.bulk_update(self.albums_to_update, ['album_songs_sting'])

        return True

    def dump_song_ids(self):
        ids_string = ''
        for album in self.albums:
            ids_string = ids_string + album.album_songs_sting + ','

        ids_sting = ids_string[:-2]

        return ids_string.split(',')[:-2]




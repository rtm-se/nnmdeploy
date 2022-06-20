import datetime
from main_page.models import ArtistModel, AlbumModel, SongModel
from profile_page.models import ListenedSongsModel, EncounteredAlbumModel
import requests

#todo figure out that fucking unix timestamp, who da fuq thought that this is a valid way to show time?
#47 years in milliseconds?
AFTER = 1484811043508


class WorkingItemsHandler:
    def __init__(self):
        self.songs_created = None
        self.albums_created = None
        self.artists_created = None

        self.album_names = {}
        self.artists_names = {}
        self.songs_ids = {}

        self.working_items = []

        self.artists_to_create = []
        self.albums_to_create = []
        self.songs_to_create = []

        self.nodes = None

    def check_and_create_items(self):
        #if there are no songs to create there are no new albums for sure, but if there's no new albums there might be new artists
        if self.songs_to_create:
            self.songs_created = SongModel.objects.bulk_create(self.songs_to_create)
            if self.albums_to_create:
                self.albums_created = AlbumModel.objects.bulk_create(self.albums_to_create)
            if self.artists_to_create:
                self.artists_created = ArtistModel.objects.bulk_create(self.artists_to_create)

    def updating_value_on_nodes(self):
        songs_to_update = []
        AlbumArtistMtM = AlbumModel.artist_name.through
        aamtm_to_create = []

        SongArtistMtM = SongModel.artist.through
        samtm_to_create = []

        for node in self.nodes:
            if node.song_update:
                node.song.refresh_from_db(fields=['id', 'album'])

                if node.artists_update:
                    for artist in node.artists:
                        print(f'updating artist {artist.name}')
                        artist.refresh_from_db(fields=['id'])
                        #if len(node.song.artist.all()) == 0:
                        samtm_to_create.append(SongArtistMtM(
                            songmodel_id=node.song.id,
                            artistmodel_id=artist.id
                        ))

                #the old way of adding artists in bulk but only for 1 track at a time
                #node.song.artist.add(*node.artists)

                if node.album_update:
                    node.album.refresh_from_db(fields=['id'])
                    for artist in node.album_artists:
                        #if node.song.album is None:
                        aamtm_to_create.append(AlbumArtistMtM(
                            albummodel_id=node.album.id,
                            artistmodel_id=artist.id
                        ))

                    #old method
                    #node.album.artist_name.add(*node.album_artists)


                node.song.album = node.album
                songs_to_update.append(node.song)

        #this creates O2n which is not ideal, i guess
        #SongModel.objects.bulk_update([node.song for node in self.nodes if node.song_update], ['album'])

        SongArtistMtM.objects.bulk_create(samtm_to_create)
        AlbumArtistMtM.objects.bulk_create(aamtm_to_create)
        SongModel.objects.bulk_update(songs_to_update, ['album'])

    def create_profile_models(self, user):
        listened_songs_list = []
        encountered_list = []
        for node in self.nodes:
            listened_songs_list.append(ListenedSongsModel(
                user=user,
                song=node.song,
                played_at=node.played_at
            ))
            # todo possibly check for songs
        for album_name in self.album_names.keys():

            if EncounteredAlbumModel.objects.filter(user=user, album__name=album_name).only('user', 'album').exists():
                pass
            else:
                encountered_list.append(EncounteredAlbumModel(
                    user=user,
                    album=self.album_names[album_name],
                    visible=True
                ))

        ListenedSongsModel.objects.bulk_create(listened_songs_list)
        EncounteredAlbumModel.objects.bulk_create(encountered_list)

        return True

class ItemDataHandler:
    ListOfNodes = []
    def __init__(self):
        self.song_update = False
        self.album_update = False
        self.artists_update = False
        self.artists = []
        self.album = None
        self.album_artists = []
        self.song = None
        self.played_at = None
        self.ListOfNodes.append(self)

# creating artist class
class SpotifyArtistNode:
    #todo redo this list as a custom que class
    ListOfNodes = []

    def __init__(self, artist_name, artist_link):
        self.artist_name = artist_name
        self.artist_link = artist_link

        self.ListOfNodes.append(self)

    def __str__(self):
        return f'{self.artist_name}'


# creating album
class SpotifyAlbumNode:
    #todo redo this list as a custom que class
    ListOfNodes = []

    def __init__(self, artist_name, album_name, cover64, cover300, cover640,  album_link, date, album_type, total_tracks):
        self.artist_name = artist_name
        self.album_name = album_name
        self.album_cover64 = cover64
        self.album_cover300 = cover300
        self.album_cover640 = cover640
        self.album_link = album_link
        self.album_date = date
        self.album_type = album_type
        self.total_tracks = total_tracks

        # appending the object to the class list
        self.ListOfNodes.append(self)

    def __str__(self):
        return f'{self.artist_name} - {self.album_name} - release{self.album_date}'


class SpotifySongNode:
    #todo redo this list as a custom que class
    ListOfNodes = []

    def __init__(self, album_name, song_name, artist_name, spotify_id, played_at, track_number):

        self.album_name = album_name
        self.song_name = song_name
        self.artist_name = artist_name
        self.spotify_id = spotify_id
        self.played_at = played_at
        self.track_number = track_number
        # appending the object to the class list
        self.ListOfNodes.append(self)


    def __str__(self):
        return f'{self.song_name}'



#todo make a linked list that will reperesent a que for adding albums


def dump_spotify_data(user, key):
    #make the request
    data_dict = get_recent_songs_data(key=key)
    if data_dict:

        items_class = parse_spotify_json(data_dict, user)
        if items_class:
            items_class.check_and_create_items()
            items_class.updating_value_on_nodes()
            items_class.create_profile_models(user)

    else:
        print('request failed')
    return True

    '''
    add_artists_to_db(nodes[0])

    list_of_album_models = add_albums_to_db(nodes[1])
    #add every new song to the data base
    #extract albums data adding class objects to the que
    add_listened_albums(user=user, list_of_album_models=list_of_album_models)
    #add all new albums to the database

    # mark new albums at the listened list
    songs_list = add_songs_to_db(nodes[2])
    # mark every song at the listened log
    add_listened_songs(user, songs_list)
    return True
    '''

def get_recent_songs_data(key):
    payload = {'limit': 50, 'after': AFTER, }
    headers = {'Authorization': f'Bearer    {key}'}
    link = 'https://api.spotify.com/v1/me/player/recently-played'
    request = requests.get(link, params=payload, headers=headers)

    # todo make a check for a response code
    if request.status_code != 200:
        return False

    #  logging a request
    #with open(f'logs/{datetime.datetime.now().strftime("%d-%m-%Y--%H-%M-%S")}-{key[10:20]}', 'x', encoding="utf-8") as file:
    #    file.write(f'{request.status_code}, \n {request.text}, \n {request.content}')

    # converting to json
    dict_request = request.json()
    return dict_request


def parse_spotify_json(dict_request, user):
    #checking if there's a played_at key in the data_dict if not the data comes from saved songs requests and needs
    #to use added at key to get the song date
    try:
        played_at_name = dict_request['items'][0]['played_at']
        played_at_name = 'played_at'
    except:
        played_at_name = 'added_at'

    local_items_handler = WorkingItemsHandler()
    for item in dict_request['items']:
        if ListenedSongsModel.objects.filter(user=user, played_at=item[played_at_name]).only('played_at').exists():
            print('node skipped')
        else:
            local_items_handler.working_items.append(item)
            data_handler_node = ItemDataHandler()

            #date
            data_handler_node.played_at = item[played_at_name]

            # check if the song already exists
            song_id = item['track']['id']
            song = SongModel.objects.filter(spotify_id=song_id).only('spotify_id', 'id')
            if song.exists():
                data_handler_node.song = song[0]
                local_items_handler.songs_ids.update({song_id: data_handler_node.song})
            else:

                # artist
                for artist in item['track']['artists']:
                    artist_name = artist['name']
                    if artist_name in local_items_handler.artists_names.keys():
                        data_handler_node.artists.append(local_items_handler.artists_names[artist_name])
                        data_handler_node.artists_update = True
                    else:
                        q_artist = ArtistModel.objects.filter(name=artist_name).only('name', 'id')

                        if q_artist.exists():
                            local_items_handler.artists_names.update({artist_name: q_artist[0]})
                            data_handler_node.artists.append(q_artist[0])
                            data_handler_node.artists_update = True
                        else:

                            artist_link = artist['external_urls']['spotify']
                            data_handler_node.artists.append(ArtistModel(name=artist_name, artist_link=artist_link))
                            data_handler_node.artists_update = True
                            local_items_handler.artists_to_create.append(data_handler_node.artists[-1])
                            local_items_handler.artists_names.update({artist_name: data_handler_node.artists[-1]})



                # album
                album_name = item['track']['album']['name']
                if album_name in local_items_handler.album_names.keys():
                    data_handler_node.album = local_items_handler.album_names[album_name]
                    data_handler_node.album_update = True
                else:
                    q_album = AlbumModel.objects.filter(name=album_name).only('name', 'id')
                    if q_album.exists():
                        local_items_handler.album_names.update({album_name: q_album[0]})
                        data_handler_node.album = q_album[0]

                    else:
                        album_cover64 = item['track']['album']['images'][2]['url']
                        album_cover300 = item['track']['album']['images'][1]['url']
                        album_cover640 = item['track']['album']['images'][0]['url']
                        album_link = item['track']['album']['external_urls']['spotify']
                        total_tracks = item['track']['album']['total_tracks']
                        album_type = item['track']['album']['album_type']

                        for album_artist in item['track']['album']['artists']:
                            try:
                                data_handler_node.album_artists.append(local_items_handler.artists_names[album_artist['name']])
                            except KeyError:
                                print('artists is not on the track')

                        if item['track']['album']['release_date_precision'] == "year":
                            album_date = item['track']['album']['release_date'] + '-01-01'
                        elif item['track']['album']['release_date_precision'] == "month":
                            album_date = item['track']['album']['release_date'] + '-01'
                        else:
                            album_date = item['track']['album']['release_date']
                        data_handler_node.album = AlbumModel(
                            name=album_name,
                            cover64=album_cover64,
                            cover300=album_cover300,
                            cover640=album_cover640,
                            link=album_link,
                            release_date=album_date,
                            album_type=album_type,
                            total_tracks=total_tracks
                        )
                        data_handler_node.album_update = True
                        local_items_handler.albums_to_create.append(data_handler_node.album)
                        local_items_handler.album_names.update({album_name: data_handler_node.album})
                data_handler_node.album_update = True


                # song
                song_id = item['track']['id']
                if song_id in local_items_handler.songs_ids.keys():
                    data_handler_node.song = local_items_handler.songs_ids[song_id]
                else:
                    song = SongModel.objects.filter(spotify_id=song_id).only('spotify_id', 'id')
                    if song.exists():
                        data_handler_node.song = song[0]
                        local_items_handler.songs_ids.update({song_id: data_handler_node.song})

                    else:
                        track_number = item['track']['track_number']
                        song_name = item['track']['name']
                        data_handler_node.song = SongModel(
                            spotify_id=song_id,
                            name=song_name,
                            track_number=track_number,
                        )
                        data_handler_node.song_update = True
                        local_items_handler.songs_to_create.append(data_handler_node.song)
                        local_items_handler.songs_ids.update({song_id: data_handler_node.song})

    if ItemDataHandler.ListOfNodes:
        local_items_handler.nodes = ItemDataHandler.ListOfNodes
        print('tracks parsing completed')
        return local_items_handler
    else:
        print('no new nodes')
        return False





def add_artists_to_db(list_of_artists):
    while list_of_artists:
        artist = list_of_artists.pop(0)
        if not ArtistModel.objects.filter(name=artist.artist_name).exists():
            ArtistModel(name=artist.artist_name, artist_link=artist.artist_link).save()
    return True


def add_albums_to_db(list_of_albums):
    list_of_album_models = []
    while list_of_albums:
        album = list_of_albums.pop(0)
        if not AlbumModel.objects.filter(name=album.album_name).exists():

            album_obj = AlbumModel(
                name=album.album_name,
                cover64=album.album_cover64,
                cover300=album.album_cover300,
                cover640=album.album_cover640,
                link=album.album_link,
                release_date=album.album_date,
                album_type=album.album_type,
                total_tracks=album.total_tracks

            )
            album_obj.save()
            album_obj.artist_name.add(ArtistModel.objects.get(name=album.artist_name))
            list_of_album_models.append(album_obj)
        else:
            list_of_album_models.append(AlbumModel.objects.get(name=album.album_name))

    return list_of_album_models


def add_listened_albums(user, list_of_album_models):
    for album in list_of_album_models:
        if not EncounteredAlbumModel.objects.filter(user=user, album=album).exists():
            obj = EncounteredAlbumModel(user=user, album=album, visible=True)
            obj.save()

    return True


def add_songs_to_db(list_of_songs):
    list_of_song_models = []
    while list_of_songs:
        song = list_of_songs.pop(0)
        #todo add better song
        if not SongModel.objects.filter(spotify_id=song.spotify_id).exists():

            song_obj = SongModel(
                spotify_id=song.spotify_id,
                name=song.song_name,
                track_number=song.track_number,
                album=AlbumModel.objects.get(name=song.album_name)
            )
            song_obj.save()
            song_obj.artist.add(ArtistModel.objects.get(name=song.artist_name))

            list_of_song_models.append({'song_obj': song_obj, 'date': song.played_at})
        else:
            list_of_song_models.append({'song_obj': SongModel.objects.get(spotify_id=song.spotify_id), 'date': song.played_at})

    return list_of_song_models


def add_listened_songs(user, list_of_song_models):
    for song_dict in list_of_song_models:
        obj = ListenedSongsModel(user=user, song=song_dict['song_obj'], played_at=song_dict['date'])
        obj.save()

    return True




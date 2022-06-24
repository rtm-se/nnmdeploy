from main_page.models import ArtistModel, SongModel, AlbumModel
from .api_call_to_model import create_song_model, create_artists_model, create_album_mode


class SpotifyDataHandler:


    class SpotifyDataNode:

        def __init__(self, data: dict, item_type: str, parent: 'SpotifyDataHandler'):
            self.parent = parent
            self.data: dict = data
            self.item_type: str = item_type
            self.item_id: str = data['id']
            if item_type == 'song':
                self.album_id: str = None
                self.song_artists_ids: list = []
                self.album_artists_ids: list = []
                self.find_or_create_song(data)
            elif item_type == 'album':
                self.album_artists_ids: list = []
                self.find_or_create_album(data)
            elif item_type == 'artist':
                self.find_or_create_artist(data)

        def find_or_create_artist(self, artist_data: dict):
            artist_spotify_id = artist_data['id']
            if artist_spotify_id in self.parent.artists:
                pass
                #artist = SpotifyDataHandler.artists[artist_spotify_id]['obj']
            else:

                if ArtistModel.objects.filter(spotify_id=artist_spotify_id).exists():
                    artist = ArtistModel.objects.get(spotify_id=artist_spotify_id)

                    self.parent.artists.update({
                        artist_spotify_id: {
                            'obj': artist,
                            'new': False
                        }
                    })
                else:
                    artist = create_artists_model(artist_data)
                    self.parent.artists.update({
                        artist_spotify_id: {
                            'obj': artist,
                            'new': True
                        }
                    })
            return artist_spotify_id

        def find_or_create_album(self, album_data: dict):
            album_spotify_id: str = album_data['id']
            if album_spotify_id in self.parent.albums:
                pass
                #album = SpotifyDataHandler.albums[album_spotify_id]['obj']
            else:
                if AlbumModel.objects.filter(spotify_id=album_spotify_id).exists():
                    album = AlbumModel.objects.get(spotify_id=album_spotify_id)
                    self.parent.albums.update({
                        album_spotify_id: {
                            'obj': album,
                            'new': False
                        }})
                else:
                    album = create_album_mode(album_data)
                    self.parent.albums.update({
                        album_spotify_id: {
                            'obj': album,
                            'new': True
                        }})
                    for artist_data in album_data['artists']:
                        self.album_artists_ids.append(self.find_or_create_artist(artist_data))
            return album_spotify_id

        def find_or_create_song(self, song_data):
            song_spotify_id: str = song_data['id']
            if song_spotify_id in self.parent.songs:
                song = self.parent.songs[song_spotify_id]['obj']
            else:
                # Checking if the song with spotify exists in the db
                if SongModel.objects.filter(spotify_id=song_spotify_id).exists():
                    song = SongModel.objects.get(spotify_id=song_spotify_id)
                    self.parent.songs.update({
                        song_spotify_id: {
                            'obj': song,
                            'new': False
                        }})
                else:
                    # if everything else fails we create new model object
                    song = create_song_model(song_data)
                    self.parent.songs.update({
                        song_spotify_id: {
                            'obj': song,
                            'new': True
                        }})
                    # find artists
                    for artist_data in song_data['artists']:
                        self.song_artists_ids.append(self.find_or_create_artist(artist_data))
                    # find songs
                    self.album_id = self.find_or_create_album(song_data['album'])

    def __init__(self, data_set: list, data_type: str):
        # Get the data

        # Supporting lists for storing new models
        self.artists: dict = {}
        self.albums: dict = {}
        self.songs: dict = {}
        self.new_models_artists: list = []
        self.new_models_albums: list = []
        self.new_models_songs: list = []
        self.data = data_set

        # self.data_type = data_type # Might be unnecessary
        self.nodes: list = []
        # Sort the data into nodes
        for item in data_set:
            self.nodes.append(self.SpotifyDataNode(item, data_type, parent=self))
        # Check for creating new models
        self.create_mew_models()
        # Check for creating new connections on items
        self.create_connections()

    def create_mew_models(self) -> None:
        # Methode that should go into each category of the SpotifyDataHandler lists and check for uncreated models
        def find_new_nodes(models_list: dict, storing_list: list) -> None:
            for item in models_list:
                if models_list[item]['new']:
                    storing_list.append(models_list[item]['obj'])

        find_new_nodes(self.songs, self.new_models_songs)
        find_new_nodes(self.albums, self.new_models_albums)
        find_new_nodes(self.artists, self.new_models_artists)

        if self.new_models_songs:
            SongModel.objects.bulk_create(self.new_models_songs)
            for song in self.new_models_songs:
                song.refresh_from_db()

        if self.new_models_albums:
            AlbumModel.objects.bulk_create(self.new_models_albums)
            for album in self.new_models_albums:
                album.refresh_from_db()

        if self.new_models_artists:
            ArtistModel.objects.bulk_create(self.new_models_artists)
            for artist in self.new_models_artists:
                artist.refresh_from_db()

    def create_connections(self):
        album_artists_mtm: list = []
        song_artists_mtm: list = []
        song_album_fk: list = []
        AlbumArtistMtM = AlbumModel.artist_name.through
        SongArtistMtM = SongModel.artist.through

        for node in self.nodes:
            if node.item_type == 'artist':
                # IF the item type is artist there's nothing to update on that model.
                pass
            elif node.item_type == 'album':
                # If the item type is album we have to check for each artist mtm
                if self.albums[node.item_id]['new']:
                    for pk in node.album_artists_ids:
                        album_artists_mtm.append(AlbumArtistMtM(
                            artistmodel_id=self.artists[pk]['obj'].id,
                            albummodel_id=self.albums[node.item_id]['obj'].id
                        ))

            elif node.item_type == 'song':
                # if the song is just created check if the album just created too and update everything
                if self.songs[node.item_id]['new']:
                    if self.albums[node.album_id]['new']:
                        for pk in node.album_artists_ids:
                            # TODO create a dictionarry of ids that will show if the object already appended to the album or song
                                album_artists_mtm.append(AlbumArtistMtM(
                                    artistmodel_id=self.artists[pk]['obj'].id,
                                    albummodel_id=self.albums[node.album_id]['obj'].id
                                ))
                    # check if there are no such connections before made in this cycle
                    self.songs[node.item_id]['obj'].album = self.albums[node.album_id][
                        'obj']
                    song_album_fk.append(self.songs[node.item_id]['obj'])

                    for artist_id in node.song_artists_ids:
                        song_artists_mtm.append(SongArtistMtM(
                            artistmodel_id=self.artists[artist_id]['obj'].id,
                            songmodel_id=self.songs[node.item_id]['obj'].id
                        ))

        SongArtistMtM.objects.bulk_create(song_artists_mtm)
        AlbumArtistMtM.objects.bulk_create(album_artists_mtm)
        SongModel.objects.bulk_update(song_album_fk, ['album'])

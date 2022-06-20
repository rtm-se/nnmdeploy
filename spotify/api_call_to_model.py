from main_page.models import ArtistModel, SongModel, AlbumModel


def create_artists_model(artist_data: dict) -> ArtistModel:
    name = artist_data['name']
    artist_link = artist_data['external_urls']['spotify']
    spotify_id = artist_data['id']
    artist = ArtistModel(
        name=name,
        artist_link=artist_link,
        spotify_id=spotify_id,
        genres=None,
    )
    if 'genres' in artist_data:
        genres = ','.join(artist_data['genres'])
        artist.genres = genres

    return artist


def create_album_mode(album_data: dict) -> AlbumModel:
    name = album_data['name']
    cover64 = album_data['images'][2]['url']
    cover300 = album_data['images'][1]['url']
    cover640 = album_data['images'][0]['url']
    link = album_data['external_urls']['spotify']
    spotify_id = album_data['id']
    if album_data['release_date_precision'] == "year":
        release_date = album_data['release_date'] + '-01-01'
    elif album_data['release_date_precision'] == "month":
        release_date = album_data['release_date'] + '-01'
    else:
        release_date = album_data['release_date']
    total_tracks = album_data['total_tracks']
    album_type = album_data['album_type']
    album = AlbumModel(
        name=name,
        cover64=cover64,
        cover300=cover300,
        cover640=cover640,
        link=link,
        spotify_id=spotify_id,
        release_date=release_date,
        total_tracks=total_tracks,
        album_type=album_type,
        album_songs_sting=None
    )
    if 'tracks' in album_data:
        album.album_songs_sting = ','.join([track_data['id'] for track_data in album_data['tracks']['items']])
    return album


def create_song_model(song_data: dict) -> SongModel:
    name = song_data['name']
    track_number = song_data['track_number']
    spotify_id = song_data['id']
    song = SongModel(
        name=name,
        track_number=track_number,
        spotify_id=spotify_id
    )
    return song

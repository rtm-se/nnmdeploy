import requests
from main_page.models import AlbumModel


def albums():
    key = input('please insert your key:\n')
    all_albums = AlbumModel.objects.all()
    counter = 0
    for album in all_albums:
        if album.total_tracks is None:
            print(f'updating {album.name}')
            try:
                make_request(album, key)
                counter += 1
            except:
                print(f'error during updating {album.name}')

    return f'update {counter} albums'


def make_request(album, key):
    album_id = album.uri()
    url = f'https://api.spotify.com/v1/albums/{album_id}'

    headers = {
        'Accept': 'application / json',
        "Content-Type": "application/json",
        'Authorization': f'Bearer    {key}'
    }
    response = requests.get(url, headers=headers)
    data = response.json()
    album.album_type = data['album_type']
    album.total_tracks = data['total_tracks']
    album.save()
    return True


if __name__ == '__main__':
    albums()

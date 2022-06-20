import requests
from spotify.models import SpotifyToken
from spotify import spotify_request_script
from profile_page.models import SpotifyLikeModel, SpotifySavedAlbumModerl
from .util import is_spotify_authenticated

def rip_likes(user):
    is_spotify_authenticated(user)
    tokens = SpotifyToken.objects.get(user=user)
    all_song_list = []
    next_check = True
    counter = 0
    while next_check:
        data = make_request(offset=counter, key=tokens.access_token)
        next_check = data['next']
        counter += 1
        #parsing json and returning a list of lists wiht class objects with extracted data
        local_items_handler = spotify_request_script.parse_spotify_json(data, user)
        #adding new artists to db
        #spotify_request_script.add_artists_to_db(nodes[0])
        if local_items_handler:
            local_items_handler.check_and_create_items()
            local_items_handler.updating_value_on_nodes()
            local_items_handler.create_profile_models(user)
            add_spotifylike(local_items_handler, user)

        #list_of_album_models = spotify_request_script.add_albums_to_db(nodes[1])
        # add every new song to the data base
        # extract albums data adding class objects to the que
        #spotify_request_script.add_listened_albums(user=user, list_of_album_models=list_of_album_models)
        # add all new albums to the database

        # mark new albums at the listened list
        #songs_list = spotify_request_script.add_songs_to_db(nodes[2])
        # mark every song at the listened log
        #spotify_request_script.add_listened_songs(user, songs_list)
        #add same songs to spotify like songs
        #add_spotifylike(user=user, list_of_song_models=songs_list)
        #adding to list to return
        #for song_pair in songs_list:
        #    all_song_list.append(song_pair['song_obj'])

    return data['total']


def make_request(offset, key):
    url = 'https://api.spotify.com/v1/me/tracks'
    payload = {
        'market': 'US',
        'limit': 50,
        'offset': f'{offset*49}'
    }
    headers = {
        'Accept': 'application / json',
        "Content-Type": "application/json",
        'Authorization': f'Bearer    {key}'
    }
    response = requests.get(url, params=payload, headers=headers)

    data = response.json()
    return data


def add_spotifylike(item_handler, user):
    updating_spotify_likes = []
    for node in item_handler.nodes:
        if not SpotifyLikeModel.objects.filter(song__id=node.song.id, user=user).exists:
            updating_spotify_likes.append(
                SpotifyLikeModel(
                    user=user,
                    song=node.song
                )
            )
    SpotifyLikeModel.objects.bulk_create(updating_spotify_likes)



def add_spotifylike_old(user, list_of_song_models):
    for song_dict in list_of_song_models:
        if not SpotifyLikeModel.objects.filter(song=song_dict['song_obj']).exists():
            obj = SpotifyLikeModel(user=user, song=song_dict['song_obj'])
            obj.save()
    return True

if __name__ == '__main__':
    pass
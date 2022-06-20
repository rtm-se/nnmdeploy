import requests
from profile_page.models import SpotifyLikeModel
from spotify.models import SpotifyToken


def record_likes(user):
    tokens = SpotifyToken.objects.get(user=user)
    likes_querry = SpotifyLikeModel.objects.filter(user=user)
    sliced_querry = slice_the_querry(likes_querry)
    for part in sliced_querry:
        string_of_ids = stingify_querry(part)
        status = record_likes_request(tokens.access_token, string_of_ids)
        print(status)

    return True


def record_likes_request(key, string_of_ids):
    url = 'https://api.spotify.com/v1/me/tracks'
    payload = {
        'ids': string_of_ids
    }
    headers = {
        'Accept': 'application / json',
        "Content-Type": "application/json",
        'Authorization': f'Bearer    {key}'
    }

    response = requests.put(url, params=payload, headers=headers)
    return response.status_code


def slice_the_querry(querry):
    list_of_slices = []
    length = len(querry)
    slices_count = length//50

    float_point = length % 50
    counter = 0
    while slices_count > counter:
        list_of_slices.append(querry[counter*50:counter*50+49])
        counter += 1

    if float_point:
        list_of_slices.append(querry[slices_count*50:length+1])

    return list_of_slices


def stingify_querry(list_of_likes):
    list_of_strings = []
    for pair in list_of_likes:
        list_of_strings.append(pair.song.spotify_id)
    string_of_urls = ','.join(list_of_strings)
    return string_of_urls


if __name__ == '__main__':
    pass
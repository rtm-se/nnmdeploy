import requests
from PIL import ImageFile
from main_page.models import AlbumModel


def change_links():
    # gett all models
    all_album_models = AlbumModel.objects.all()
    # grab one model
    for album in all_album_models:
        cover_size = get_the_image_width(album.cover64)
        # check if it's cover64 link got 640 width
        if cover_size == (640, 640):
            print(album.name)
        # change links places
            cover64x = album.cover64
            album.cover64 = album.cover640
            album.cover640 = cover64x
        # save
            album.save()
    print('finishing')
    return True


def get_the_image_width(link):
    resume_header = {'Range': 'bytes=0-2000000'}
    data = requests.get(link, stream=True, headers=resume_header).content

    p = ImageFile.Parser()
    p.feed(data)
    if p.image:
        return p.image.size


if __name__ == '__main__':
    change_links()

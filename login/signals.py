#from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db.models.signals import post_save

from profile_page.models import ProfileModel

#@receiver(post_save, sender=User)
def user_created_handler(instance, created, **kwargs):
    if kwargs['raw']:
        return
    print(created)
    if created:
        profile = ProfileModel(user=instance)
        profile.save()
    else:
        #do logic in case of updating user profile
        pass


post_save.connect(user_created_handler, sender=User)

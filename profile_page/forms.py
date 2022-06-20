from django.forms import ModelForm, CheckboxInput, Textarea, PasswordInput, CharField, RadioSelect
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm

from django.utils.translation import gettext_lazy as _
from . import models


class ReviewModelForm(ModelForm):
    class Meta:
        model = models.ReviewModel
        fields = ['recommended', 'body']

        widgets = {
            'body': Textarea(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Write your review here',
                'type': 'text',
                'rows': 3
                                    }),


        }


class ListenedAlbumsCheckBoxForm(ModelForm):
    class Meta:
        model = models.EncounteredAlbumModel
        fields = ['visible']
        widgets = {
            'visible': CheckboxInput(attrs={
                'name': models.EncounteredAlbumModel.album
            })
        }
        help_texts = {
            'visible': _('Some useful help text.'),

        }
        labels = {
            'visible': _(''),
        }


class UserProfileForm(ModelForm):
    class Meta:
        model = models.ProfileModel
        fields = ['pfp', 'bio', 'reviews_visibility', 'likes_visibility', 'encountered_visibility']


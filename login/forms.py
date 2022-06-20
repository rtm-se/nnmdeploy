from django.forms import PasswordInput, CharField
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm


class PasswordChangedForm(PasswordChangeForm):
    old_password = CharField(max_length=100, widget=PasswordInput(attrs={'class': 'form-control', 'type': 'password'}))
    new_password1 = CharField(max_length=100, widget=PasswordInput(attrs={'class': 'form-control', 'type': 'password'}))
    new_password2 = CharField(max_length=100, widget=PasswordInput(attrs={'class': 'form-control', 'type': 'password'}))

    class Meta:
        model = User
        fields = ['old_password','new_password1', 'new_password2']

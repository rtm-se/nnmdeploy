from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .forms import PasswordChangedForm
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from profile_page.models import ProfileModel
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views

# Create your views here.


def viewpage(request):
    return render(request, 'login/login_page.html')


def login_page(request):
    if request.user.is_authenticated:
        return redirect(reverse('main_page:home'))

    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, "User doesn't exist")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect(reverse('main_page:home'))
        else:
            messages.error(request, "wrong credentials")

    context = {}

    return render(request, 'login/login_page.html', context)

@login_required(login_url='main_page:home')
def logout_user(request):
    logout(request)
    return redirect(reverse('main_page:home'))

def register_view(request):
    forms = UserCreationForm()

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            #profile = ProfileModel(user=user)
            user.save()
            #profile.save()
            login(request, user)
            return redirect('main_page:home')
        else:
            messages.error(request, 'an error occurred during registration')

    return render(request, 'login/register.html', {'forms': forms})
    pass


class PasswordChangeView(auth_views.PasswordChangeView):
    form_class = PasswordChangedForm
    success_url = reverse_lazy('login:pass_succ')
    template_name = 'login/change_password.html'


def pass_change_success(request):
    return render(request, 'login/success_pass.html')

from django.urls import path
from django.contrib.auth import views as auth_views
from .views import login_page, logout_user, register_view, PasswordChangeView, pass_change_success
app_name = 'login'

urlpatterns = [
    path('', login_page, name='login'),
    path('logout/', logout_user, name='logout'),
    path('register/', register_view, name='register'),
    path('password/', PasswordChangeView.as_view(), name='pass_change'),
    path('password_success/', pass_change_success, name='pass_succ')


]
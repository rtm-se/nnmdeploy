from django.shortcuts import render, HttpResponse

# Create your views here.

def test_view(request):

    return render(request, 'testapp/test_app.html')

def bruh(request):
    print('bruh', request.user.username)
    return HttpResponse('bruh')

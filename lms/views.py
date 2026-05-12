from django.shortcuts import render

def index(request):
    return render(request, 'lms/index.html')

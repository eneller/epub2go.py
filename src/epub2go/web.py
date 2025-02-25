# run using `django-admin runserver --pythonpath=. --settings=web`
from django.urls import path
from django.http import HttpResponse
from django.shortcuts import redirect, render 
import requests

import utils
import json
DEBUG = True
ROOT_URLCONF = __name__
SECRET_KEY='1'
TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [
                'templates/'
            ],
        },
    ]

def home(request):
    title = 'epub2go'
    items = json.load(open('dict.json', 'r'))
    return render(request, 'index.html', locals())

urlpatterns = [
    path('', home, name='homepage'),
]

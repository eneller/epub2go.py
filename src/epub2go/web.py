# run using `django-admin runserver --pythonpath=. --settings=web`
from django.urls import path
from django.http import HttpResponse, HttpRequest
from django.shortcuts import redirect, render 
import requests

from convert import GBConvert, allbooks_url
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

def root(request: HttpRequest):
    title = 'epub2go'
    targetParam = request.GET.get('t', None)
    if targetParam is not None:
        getEpub(targetParam)
    return render(request, 'index.html', locals())

urlpatterns = [
    path('', root, name='root'),
]

def getEpub(param):
    # TODO validate / sanitize input
    # TODO check for existing file and age
    # TODO download
    # TODO redirect to loading page
    # TODO redirect to download page
    raise NotImplementedError

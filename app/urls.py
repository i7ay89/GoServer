__author__ = 'user'

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^login$', views.login, name='login'),
    url(r'^register/(?P<mac_address>[0-9a-fA-F][12])$', views.register_mac, name='register_mac'),
]

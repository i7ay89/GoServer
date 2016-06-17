__author__ = 'user'

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^login$', views.login, name='login'),
    url(r'^register_mac$', views.register_mac, name='register_mac'),
    url(r'^sync$', views.sync, name='sync'),
    url(r'^create_new_user$', views.create_new_user, name='create_new_user'),
    url(r'^get_last_events$', views.get_last_events, name='get_last_events'),
    url(r'snapshots/(?P<image_id>[0-9]+)$', views.get_snapshot, name='get_snapshot'),
    url(r'^arm$', views.arm, name='arm'),
    url(r'^unarm$', views.unarm, name='unarm'),
]

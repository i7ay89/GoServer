__author__ = 'user'

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^login$', views.login, name='login'),
    url(r'^register_mac$', views.register_mac, name='register_mac'),
    url(r'^sync$', views.sync, name='sync'),
    url(r'^new_user$', views.create_new_user, name='new_user'),
    url(r'^remove_user$', views.remove_user, name='remove_user'),
    url(r'^recent_events$', views.get_recent_events, name='recent_events'),
    url(r'snapshots/(?P<image_id>[0-9]+)$', views.get_snapshot, name='get_snapshot'),
    url(r'^arm$', views.arm, name='arm'),
    url(r'^disarm$', views.disarm, name='disarm'),
    url(r'^status$', views.get_status, name='status'),
    url(r'^whos_home$', views.whos_home, name='whos_home'),
    url(r'^users_list$', views.get_all_users, name='users_list'),
    url(r'^my_info$', views.get_my_permission, name='my_info'),
    url(r'^set_code$', views.set_code, name='set_code'),
]

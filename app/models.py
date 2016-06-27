from __future__ import unicode_literals
from utils import cookie_length
from django.db import models


class AppUsers(models.Model):
    UID = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=20)
    password_hash = models.CharField(max_length=32)
    cookie = models.CharField(max_length=cookie_length, default='', blank=True)


class Permissions(models.Model):
    user = models.ForeignKey(AppUsers, primary_key=True, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10)


class Events(models.Model):
    event_type = models.CharField(max_length=20)
    description = models.CharField(max_length=100)
    timestamp = models.DateTimeField(blank=False, editable=True)
    severity = models.CharField(max_length=10)


class MacToUser(models.Model):
    mac_address = models.CharField(max_length=17)
    user = models.ForeignKey(AppUsers, blank=False)


class UnreadEvents(models.Model):
    event = models.ForeignKey(Events)
    user = models.ForeignKey(AppUsers)


class ArmsLog(models.Model):
    user = models.ForeignKey(AppUsers, blank=False)
    action = models.CharField(max_length=6, blank=False)
    timestamp = models.DateTimeField(blank=False, editable=True)


class Armed(models.Model):
    armed = models.BooleanField(blank=False)

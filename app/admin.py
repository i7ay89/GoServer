from django.contrib import admin
from .models import AppUsers, Permissions, Events, UnreadEvents
# Register your models here.

admin.site.register(AppUsers)
admin.site.register(Permissions)
admin.site.register(Events)
admin.site.register(UnreadEvents)
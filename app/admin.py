from django.contrib import admin
from .models import AppUsers, Permissions
# Register your models here.

admin.site.register(AppUsers)
admin.site.register(Permissions)

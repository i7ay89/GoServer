# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AppUsers',
            fields=[
                ('UID', models.IntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=20)),
                ('password_hash', models.CharField(max_length=32)),
                ('cookie', models.CharField(default=None, max_length=25, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ArmsLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('action', models.CharField(max_length=6)),
                ('timestamp', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Events',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('event_type', models.CharField(max_length=20)),
                ('description', models.CharField(max_length=100)),
                ('timestamp', models.DateTimeField()),
                ('severity', models.CharField(max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='MacToUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('mac_address', models.CharField(max_length=17)),
            ],
        ),
        migrations.CreateModel(
            name='UnreadEvents',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('event', models.ForeignKey(to='app.Events')),
            ],
        ),
        migrations.CreateModel(
            name='Permissions',
            fields=[
                ('user', models.ForeignKey(primary_key=True, serialize=False, to='app.AppUsers')),
                ('user_type', models.CharField(max_length=10)),
            ],
        ),
        migrations.AddField(
            model_name='unreadevents',
            name='user',
            field=models.ForeignKey(to='app.AppUsers'),
        ),
        migrations.AddField(
            model_name='mactouser',
            name='user',
            field=models.ForeignKey(to='app.AppUsers'),
        ),
        migrations.AddField(
            model_name='armslog',
            name='user',
            field=models.ForeignKey(to='app.AppUsers'),
        ),
    ]

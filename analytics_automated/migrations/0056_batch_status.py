# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-11-14 12:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analytics_automated', '0055_auto_20171113_1531'),
    ]

    operations = [
        migrations.AddField(
            model_name='batch',
            name='status',
            field=models.IntegerField(choices=[(0, 'Submitted'), (1, 'Running'), (2, 'Complete'), (3, 'Error'), (4, 'Crash')], default=0),
        ),
    ]
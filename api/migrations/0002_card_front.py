# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-08 11:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='front',
            field=models.TextField(default='front'),
            preserve_default=False,
        ),
    ]
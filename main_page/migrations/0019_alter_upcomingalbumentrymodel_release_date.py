# Generated by Django 4.0.3 on 2022-04-06 08:29

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_page', '0018_rename_song_position_songmodel_track_number_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='upcomingalbumentrymodel',
            name='release_date',
            field=models.DateField(default=datetime.date(2022, 4, 6)),
        ),
    ]

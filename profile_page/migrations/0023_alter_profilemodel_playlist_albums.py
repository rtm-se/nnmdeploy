# Generated by Django 4.0.3 on 2022-04-25 20:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_page', '0030_alter_upcomingalbumentrymodel_release_date'),
        ('profile_page', '0022_profilemodel_encountered_visibility_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profilemodel',
            name='playlist_albums',
            field=models.ManyToManyField(blank=True, to='main_page.albummodel'),
        ),
    ]

# Generated by Django 4.0.3 on 2022-06-15 08:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_page', '0034_artistmodel_spotify_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='albummodel',
            name='spotify_id',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]

# Generated by Django 5.1.1 on 2024-11-14 23:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0005_alter_athlete_dojo'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='athlete',
            name='dojo',
        ),
    ]

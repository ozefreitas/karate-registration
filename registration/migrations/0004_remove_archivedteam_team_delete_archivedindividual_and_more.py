# Generated by Django 5.1.1 on 2025-02-28 11:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0003_alter_archivedteam_team'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='archivedteam',
            name='team',
        ),
        migrations.DeleteModel(
            name='ArchivedIndividual',
        ),
        migrations.DeleteModel(
            name='ArchivedTeam',
        ),
    ]

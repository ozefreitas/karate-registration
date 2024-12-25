# Generated by Django 5.1.4 on 2024-12-24 19:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0021_alter_athlete_additional_emails'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArchivedAthlete',
            fields=[
                ('athlete_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='registration.athlete')),
                ('archived_date', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('registration.athlete',),
        ),
    ]

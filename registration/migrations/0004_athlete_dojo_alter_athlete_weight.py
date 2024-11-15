# Generated by Django 5.1.1 on 2024-11-14 23:10

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0003_athlete_additional_emails_athlete_weight'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='athlete',
            name='dojo',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='athlete',
            name='weight',
            field=models.CharField(choices=[('Juvenil', [('-47', '-47Kg'), ('+47', '+47Kg')]), ('Cadete', [('-57', '-57Kg'), ('+57', '+57Kg')]), ('Júnior', [('-65', '-65Kg'), ('+65', '+65Kg')]), ('Sénior e Veterano', [('-75', '-75Kg'), ('+75', '+75Kg')])], default='10', max_length=10, verbose_name='Peso'),
        ),
    ]

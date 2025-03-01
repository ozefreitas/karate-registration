# Generated by Django 5.1.1 on 2024-12-09 21:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dojos', '0004_alter_profile_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='competitionsdetails',
            name='has_ended',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='profile',
            name='cellphone_number',
            field=models.IntegerField(default=123456789, verbose_name='Número de telemóvel pessoal'),
        ),
        migrations.AddField(
            model_name='profile',
            name='dojo_contact',
            field=models.IntegerField(default=123456789, verbose_name='Contacto do Dojo'),
        ),
    ]

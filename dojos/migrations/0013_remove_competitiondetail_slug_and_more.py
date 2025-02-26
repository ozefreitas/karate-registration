# Generated by Django 5.1.4 on 2025-02-26 10:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dojos', '0012_competitiondetail_slug'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='competitiondetail',
            name='slug',
        ),
        migrations.AlterField(
            model_name='competitiondetail',
            name='id',
            field=models.SlugField(blank=True, max_length=100, primary_key=True, serialize=False, unique=True),
        ),
    ]

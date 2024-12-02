# Generated by Django 5.1.3 on 2024-12-02 12:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0019_teams_athlete4_teams_athlete5_alter_teams_athlete3'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeamFilters',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.CharField(blank=True, choices=[('category', 'Categoria'), ('gender', 'Género'), ('match_type', 'Prova')], max_length=20, null=True, verbose_name='Ordenar por')),
                ('filter', models.CharField(blank=True, choices=[('category', 'Categoria'), ('gender', 'Género'), ('match_type', 'Prova')], max_length=20, null=True, verbose_name='Filtrar por')),
                ('search', models.CharField(blank=True, max_length=99, null=True, verbose_name='Procurar')),
            ],
        ),
        migrations.RenameModel(
            old_name='Filters',
            new_name='AthleteFilters',
        ),
    ]

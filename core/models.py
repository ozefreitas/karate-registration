from django.db import models
from .constants import GRADUATIONS, GENDERS

# Create your models here.

class Category(models.Model):
    name = models.CharField("Escalão", max_length=100)
    min_age = models.PositiveSmallIntegerField("Idade Mínima (inclusivé)", null=True, blank=True)
    max_age = models.PositiveSmallIntegerField("Idade Máxima (inclusivé)", null=True, blank=True)
    min_grad = models.CharField("Graduação Mínima (inclusivé)", max_length=4, choices=GRADUATIONS, null=True, blank=True)
    max_grad = models.CharField("Graduação Máxima (inclusivé)", max_length=4, choices=GRADUATIONS, null=True, blank=True)
    min_weight = models.PositiveSmallIntegerField("Peso Mínimo (inclusivé)", null=True, blank=True)
    max_weight = models.PositiveSmallIntegerField("Peso Máximo (inclusivé)", null=True, blank=True)
    gender = models.CharField("Género", choices=GENDERS, max_length=10)
    creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self): 
        return "{} {}".format(self.name, self.gender)


class Ranking(models.Model):
    pass
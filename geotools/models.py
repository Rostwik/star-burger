from django.db import models

from django.utils import timezone


class Location(models.Model):
    address = models.CharField('Адрес', max_length=300, unique=True)
    lat = models.DecimalField('Широта', max_digits=10, decimal_places=5, null=True)
    long = models.DecimalField('Долгота', max_digits=10, decimal_places=5, null=True)
    geo_request_date = models.DateTimeField('Дата запроса', default=timezone.now)

    def __str__(self):
        return self.address

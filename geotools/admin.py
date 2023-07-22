from django.contrib import admin

from geotools.models import Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    pass

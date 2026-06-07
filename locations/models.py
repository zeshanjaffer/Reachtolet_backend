from django.db import models


class State(models.Model):
    """US state metadata (from legacy states_capitals table)."""

    legacy_id = models.IntegerField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=50)
    abbr = models.CharField(max_length=2, db_index=True)
    capital = models.CharField(max_length=50)
    coordinates = models.CharField(max_length=50)
    latitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    enabled = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    country_id = models.BigIntegerField(null=True, blank=True)
    image = models.CharField(max_length=191, blank=True, default='')
    region = models.CharField(max_length=191, blank=True, default='')

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['abbr']),
            models.Index(fields=['enabled']),
        ]

    def __str__(self):
        return f'{self.name} ({self.abbr})'


class City(models.Model):
    """US city/town metadata (from legacy states_cities table)."""

    legacy_id = models.IntegerField(unique=True, null=True, blank=True)
    state_abbr = models.CharField(max_length=2, db_index=True)
    name = models.CharField(max_length=50, db_index=True)
    coordinates = models.CharField(max_length=100)
    enabled = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    country_id = models.BigIntegerField(null=True, blank=True)
    image = models.CharField(max_length=191, blank=True, default='')
    county_name = models.CharField(max_length=191, blank=True, default='')
    state_name = models.CharField(max_length=191, blank=True, default='')
    zip_codes = models.TextField(blank=True, default='')
    place_type = models.CharField(max_length=191, blank=True, default='')
    latitude = models.CharField(max_length=191, blank=True, default='')
    longitude = models.CharField(max_length=191, blank=True, default='')
    area_code = models.CharField(max_length=191, blank=True, default='')
    population = models.CharField(max_length=191, blank=True, default='')
    households = models.CharField(max_length=191, blank=True, default='')
    median_income = models.CharField(max_length=191, blank=True, default='')
    land_area = models.CharField(max_length=191, blank=True, default='')
    water_area = models.CharField(max_length=191, blank=True, default='')
    time_zone = models.CharField(max_length=191, blank=True, default='')

    class Meta:
        ordering = ['state_abbr', 'name']
        verbose_name_plural = 'cities'
        indexes = [
            models.Index(fields=['state_abbr', 'name']),
            models.Index(fields=['enabled']),
        ]

    def __str__(self):
        return f'{self.name}, {self.state_abbr}'


class CityBoundary(models.Model):
    """GeoJSON-like polygon boundaries per city (from legacy city_boundaries table)."""

    legacy_id = models.IntegerField(unique=True, null=True, blank=True)
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100, db_index=True)
    boundary = models.JSONField()
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'city boundaries'
        constraints = [
            models.UniqueConstraint(fields=['city', 'state'], name='uniq_city_boundary_city_state'),
        ]

    def __str__(self):
        return f'{self.city}, {self.state}'


class StateBoundary(models.Model):
    """GeoJSON-like polygon boundaries per state (from legacy state_boundaries table)."""

    legacy_id = models.IntegerField(unique=True, null=True, blank=True)
    state = models.CharField(max_length=100, unique=True)
    boundary = models.JSONField()
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'state boundaries'

    def __str__(self):
        return self.state

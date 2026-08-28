from django.db import models


class Creature(models.Model):
    class Element(models.TextChoices):
        FIRE = "FIRE", "Fire"
        WATER = "WATER", "Water"
        EARTH = "EARTH", "Earth"
        AIR = "AIR", "Air"
        NEUTRAL = "NEUTRAL", "Neutral"
        LEGENDARY = "LEGENDARY", "Legendary"

    name = models.CharField(max_length=100, unique=True)
    element = models.CharField(max_length=20, choices=Element.choices)
    classification = models.CharField(max_length=50, blank=True)
    era_location = models.CharField(max_length=100, blank=True)

    lp = models.PositiveIntegerField()
    attack = models.PositiveIntegerField()
    defense = models.PositiveIntegerField()
    accuracy = models.PositiveIntegerField()
    evasion_speed = models.PositiveIntegerField()
    crit_rate = models.PositiveIntegerField()

    sprite = models.ImageField(upload_to='creatures/', blank=True, null=True)

    def __str__(self):
        return self.name

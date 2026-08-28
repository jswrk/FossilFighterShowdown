from django.contrib import admin
from .models import Creature


@admin.register(Creature)
class CreatureAdmin(admin.ModelAdmin):
    list_display = ("name", "element", "classification", "lp", "attack",
                    "defense", "accuracy", "evasion_speed", "crit_rate")
    list_filter = ("element", "classification")

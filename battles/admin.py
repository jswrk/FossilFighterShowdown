from django.contrib import admin
from .models import Creature, Move, SupportEffect, TeamSkillGroup, PassiveSkill, DiscoveredLocation


@admin.register(TeamSkillGroup)
class TeamSkillGroupAdmin(admin.ModelAdmin):
    list_display = ("number", "name")


class MoveInline(admin.TabularInline):
    model = Move
    extra = 1


class SupportEffectInline(admin.StackedInline):
    model = SupportEffect
    extra = 1


@admin.register(Creature)
class CreatureAdmin(admin.ModelAdmin):
    list_display = ("name", "genus", "element", "creature_class",
                    "diet", "size_category", "lp", "attack", "defense",
                    "accuracy", "evasion_speed", "crit_rate")
    list_filter = ("element", "creature_class", "diet", "size_category")
    filter_horizontal = ("team_skill_groups", "discovered_locations",)
    fields = (
        "number",
        "name",
        "genus",
        "element",
        "creature_class",
        "size_category",
        "diet",
        "era",
        "dig_site",
        "discovered_locations",
        "lp",
        "attack",
        "defense",
        "accuracy",
        "evasion_speed",
        "crit_rate",
        "status_resistance",
        "sz_damage_multiplier",
        "sprite",
        "team_skill_groups",
    )
    inlines = [MoveInline, SupportEffectInline]


@admin.register(PassiveSkill)
class PassiveSkillAdmin(admin.ModelAdmin):
    list_display = ("creature", "name", "effect")


@admin.register(DiscoveredLocation)
class DiscoveredLocationAdmin(admin.ModelAdmin):
    list_display = ("name",)

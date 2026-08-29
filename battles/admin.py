from django.contrib import admin
from .models import Creature, Move, SupportEffect, SupportEffectStat, TeamSkillGroup, TeamSkill, PassiveSkill


@admin.register(TeamSkillGroup)
class TeamSkillGroupAdmin(admin.ModelAdmin):
    list_display = ("number", "name")


@admin.register(TeamSkill)
class TeamSkillAdmin(admin.ModelAdmin):
    list_display = ("creature", "name", "damage", "fp_cost", "group")
    list_filter = ("group",)


class MoveInline(admin.TabularInline):
    model = Move
    extra = 1


class SupportEffectStatInline(admin.TabularInline):
    model = SupportEffectStat
    extra = 1


@admin.register(Creature)
class CreatureAdmin(admin.ModelAdmin):
    list_display = ("name", "genus", "element", "creature_class", "group",
                    "diet", "size_category", "lp", "attack", "defense",
                    "accuracy", "evasion_speed", "crit_rate")
    list_filter = ("element", "creature_class", "group", "diet", "size_category")
    filter_horizontal = ("team_skill_groups",)
    fields = (
        "number",
        "name",
        "element",
        "genus",
        "group",
        "era",
        "length_ft",
        "length_m",
        "size_category",
        "diet",
        "dig_site",
        "discovered_location",
        "creature_class",
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
    inlines = [MoveInline]


@admin.register(SupportEffect)
class SupportEffectAdmin(admin.ModelAdmin):
    list_display = ("creature", "target")
    list_filter = ("target",)
    inlines = [SupportEffectStatInline]


@admin.register(PassiveSkill)
class PassiveSkillAdmin(admin.ModelAdmin):
    list_display = ("creature", "name", "effect")

from django.contrib import admin
from .models import Creature, Move, SupportEffect, StatusEffect, TeamSkillGroup, PassiveSkill, DiscoveredLocation, PlayerProfile, Team, TeamSlot, BattleRoom, BattleState, BattleCreatureState


class MoveInline(admin.TabularInline):
    model = Move
    extra = 1


class TeamSlotInline(admin.TabularInline):
    model = TeamSlot
    extra = 1


class SupportEffectInline(admin.StackedInline):
    model = SupportEffect
    extra = 1


class BattleCreatureStateInline(admin.TabularInline):
    model = BattleCreatureState
    extra = 1


@admin.register(TeamSkillGroup)
class TeamSkillGroupAdmin(admin.ModelAdmin):
    list_display = ("number", "name")


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


@admin.register(StatusEffect)
class StatusEffectAdmin(admin.ModelAdmin):
    list_display = ("name", "is_positive", "duration_turns")


@admin.register(DiscoveredLocation)
class DiscoveredLocationAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "wins", "losses")


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "created_at")
    inlines = [TeamSlotInline]


@admin.register(BattleRoom)
class BattleRoomAdmin(admin.ModelAdmin):
    list_display = ("room_code", "host", "guest", "status", "winner", "created_at")
    list_filter = ("status",)
    readonly_fields = ("room_code", "created_at")


@admin.register(BattleState)
class BattleStateAdmin(admin.ModelAdmin):
    list_display = ("room", "host_ez_turns_left", "guest_ez_turns_left")
    inlines = [BattleCreatureStateInline]

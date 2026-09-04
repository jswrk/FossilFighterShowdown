import random
from .models import PassiveSkill, SupportEffect, BattleCreatureState

# constants
PARTING_BLOW_LP_THRESHOLD_PERCENT = 10


# returns true iff all 3 vivos share at least 1 TeamSkillGroup
def team_skill_eligible(az_creature, sz1_creature, sz2_creature):
    az_groups = set(az_creature.team_skill_groups.all())
    sz1_groups = set(sz1_creature.team_skill_groups.all())
    sz2_groups = set(sz2_creature.team_skill_groups.all())
    return bool(az_groups & sz1_groups & sz2_groups)


# returns the AZ's team skill
def legal_team_skill_moves(az_creature, sz1_creature, sz2_creature):
    if not team_skill_eligible(az_creature, sz1_creature, sz2_creature):
        return az_creature.moveset.none()
    return az_creature.moveset.filter(is_team_skill=True)


# parting blow validation helper
def _apply_parting_blow(creature_state, base_stat, percent_field):
    try:
        skill = creature_state.creature.passive_skill
    except PassiveSkill.DoesNotExist:
        return base_stat

    if skill.name != PassiveSkill.Name.PARTING_BLOW:
        return base_stat

    threshold = creature_state.creature.lp * (PARTING_BLOW_LP_THRESHOLD_PERCENT / 100)

    if creature_state.current_lp > threshold:
        return base_stat

    percent = getattr(skill, percent_field)

    if percent is None:
        return base_stat

    return base_stat * (1 + percent / 100)


# support effect validation helper
def _support_magnitude(creature_state, magnitude_field):
    if creature_state.zone != BattleCreatureState.Zone.AZ:
        return 0

    total = 0
    sz_states = creature_state.battle_state.creature_states.filter(
        zone__in=[BattleCreatureState.Zone.SZ1, BattleCreatureState.Zone.SZ2])

    for sz_state in sz_states:
        try:
            effect = sz_state.creature.support_effect
        except SupportEffect.DoesNotExist:
            continue

        magnitude = getattr(effect, magnitude_field)
        if magnitude is None:
            continue

        same_side_self_az = (
            effect.target == SupportEffect.Target.SELF_AZ
            and sz_state.side == creature_state.side
        )

        opposing_side_enemy_az = (
            effect.target == SupportEffect.Target.ENEMY_AZ
            and sz_state.side != creature_state.side
        )

        if same_side_self_az or opposing_side_enemy_az:
            total += magnitude

    return total


# support effect calculation helper
def _support_multiplier(creature_state, magnitude_field):
    return 1 + (_support_magnitude(creature_state, magnitude_field) / 100)

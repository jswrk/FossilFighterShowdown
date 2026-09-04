import random
from .models import PassiveSkill, SupportEffect, StatusEffect, BattleCreatureState, Creature

# constants
PARTING_BLOW_LP_THRESHOLD_PERCENT = 10
ELEMENT_CYCLE = [Creature.Element.FIRE, Creature.Element.EARTH,
                 Creature.Element.AIR, Creature.Element.WATER]
CRITICAL_HIT_MULTIPLIER = 1.5


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


# damage calculaiton
def calculate_damage(attacker_state, defender_state, move):
    if move.damage is None:
        return 0

    effective_attack = _apply_parting_blow(
        attacker_state, attacker_state.creature.attack, "attack_percent")
    effective_defense = _apply_parting_blow(
        defender_state, defender_state.creature.defense, "defense_percent")

    attack_support = _support_multiplier(attacker_state, "attack_magnitude")
    defense_support = _support_multiplier(defender_state, "defense_magnitude")

    base = ((effective_attack + move.damage) * attack_support) - \
        (effective_defense * defense_support)

    sz_zones = (BattleCreatureState.Zone.SZ1, BattleCreatureState.Zone.SZ2)
    range_multiplier = attacker_state.creature.sz_damage_multiplier if attacker_state.zone in sz_zones else 1.0

    random_multiplier = _random_multiplier()
    element_multiplier = _element_multiplier(
        attacker_state.creature.element, defender_state.creature.element)
    crit_multiplier = _crit_multiplier(attacker_state.creature.crit_rate)

    damage = base * random_multiplier * element_multiplier * range_multiplier * crit_multiplier
    return max(0, round(damage))


# apples/refreshes status effect
def apply_status(creature_state, status):
    confuse_names = (StatusEffect.Name.CONFUSE, StatusEffect.Name.SUPER_CONFUSE)
    if creature_state.creature.status_immune and status.name not in confuse_names:
        return

    creature_state.active_status = status
    creature_state.status_turns_remaining = status.duration_turns
    creature_state.save(update_fields=["active_status", "status_turns_remaining"])


def tick_status(creature_state):
    if creature_state.active_status is None:
        return

    creature_state.status_turns_remaining -= 1

    if creature_state.status_turns_remaining <= 0:
        cure_status(creature_state)
        return

    creature_state.save(update_fields=["active_status", 'status_turns_remaining'])


def cure_status(creature_state):
    if creature_state.active_status is None:
        return

    creature_state.active_status = None
    creature_state.status_turns_remaining = None
    creature_state.save(update_fields=["active_status", "status_turns_remaining"])


'''helper functions'''


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


# support effects calculation helper
def _support_multiplier(creature_state, magnitude_field):
    return 1 + (_support_magnitude(creature_state, magnitude_field) / 100)


# element calculations helper
def _element_multiplier(attacker_element, defender_element):
    if attacker_element not in ELEMENT_CYCLE or defender_element not in ELEMENT_CYCLE:
        return 1.0

    index = ELEMENT_CYCLE.index(attacker_element)
    beats = ELEMENT_CYCLE[(index + 1) % 4]
    loses_to = ELEMENT_CYCLE[(index - 1) % 4]

    if defender_element == beats:
        return 1.5
    if defender_element == loses_to:
        return 0.75
    return 1.0


# random multiplier helper
def _random_multiplier():
    return random.triangular(0.95, 1.05, 1.00)


# crit multiplier helper
def _crit_multiplier(crit_rate):
    return CRITICAL_HIT_MULTIPLIER if random.randint(1, 100) <= crit_rate else 1.0

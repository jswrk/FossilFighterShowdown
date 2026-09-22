import random
from .models import PassiveSkill, SupportEffect, StatusEffect, Move, BattleCreatureState, Creature

# constants
PARTING_BLOW_LP_THRESHOLD_PERCENT = 10
ELEMENT_CYCLE = [Creature.Element.FIRE, Creature.Element.EARTH,
                 Creature.Element.AIR, Creature.Element.WATER]
CRITICAL_HIT_MULTIPLIER = 1.5


# exceptions
class IllegalMoveError(Exception):
    pass


class EmptyTransformPoolError(Exception):
    pass


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


# fp check
def is_move_legal(actor_state, move):
    return actor_state.current_fp >= move.fp_cost


# fp deduction
def spend_fp(actor_state, move):
    actor_state.current_fp = max(0, actor_state.current_fp - move.fp_cost)
    actor_state.save(update_fields=["current_fp"])


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


# status effect timer
def tick_status(creature_state):
    if creature_state.active_status is None:
        return

    creature_state.status_turns_remaining -= 1

    if creature_state.status_turns_remaining <= 0:
        cure_status(creature_state)
        return

    creature_state.save(update_fields=["active_status", 'status_turns_remaining'])


# cures status effect
def cure_status(creature_state):
    if creature_state.active_status is None:
        return

    creature_state.active_status = None
    creature_state.status_turns_remaining = None
    creature_state.save(update_fields=["active_status", "status_turns_remaining"])


# vivo transformation
def transform(creature_state, move):
    pool = list(move.transforms_into.all())

    if not pool:
        raise EmptyTransformPoolError(
            f"{move.name} has TRANSFORMS but no transforms_into creatures.")

    new_creature = random.choice(pool)

    creature_state.creature = new_creature
    creature_state.current_lp = new_creature.lp

    creature_state.active_status = None
    creature_state.status_turns_remaining = None

    creature_state.save(update_fields=["creature", "current_lp",
                        "active_status", "status_turns_remaining"])

    return new_creature


# secondary effect
def apply_secondary_effect(attacker_state, defender_state, move):
    if not move.secondary_effect:
        return None

    roll_succeeded = random.randint(1, 100) <= move.secondary_effect_success_rate

    if not roll_succeeded:
        return None

    if move.secondary_effect == Move.SecondaryEffect.TRANSFORMS:
        return transform(attacker_state, move)

    return None


# link move chance roll
def trigger_link_roll(actor_state):
    if actor_state.zone != BattleCreatureState.Zone.AZ:
        return []

    sz_allies = actor_state.battle_state.creature_states.filter(
        side=actor_state.side,
        zone__in=[BattleCreatureState.Zone.SZ1, BattleCreatureState.Zone.SZ2]
    )

    triggered = []

    for ally_state in sz_allies:
        link_move = ally_state.creature.moveset.filter(is_link_skill=True).first()
        if link_move is None:
            continue

        if random.randint(1, 100) <= link_move.link_chance_percent:
            triggered.append((ally_state, link_move))

    return triggered


# single hit damage & status infliction
def resolve_hit(attacker_state, defender_state, move):
    damage = calculate_damage(attacker_state, defender_state, move)

    defender_state.current_lp = max(0, defender_state.current_lp - damage)
    defender_state.save(update_fields=["current_lp"])

    if move.inflicts_status is not None:
        status_attempted = random.randint(1, 100) <= move.status_success_rate
        if status_attempted:
            status_resisted = random.randint(1, 100) <= defender_state.creature.status_resistance
            if not status_resisted:
                apply_status(defender_state, move.inflicts_status)

    return damage


# multi hit move execution + secondary effect + link follow-up
def execute_move(attacker_state, defender_state, move):
    if not is_move_legal(attacker_state, move):
        raise IllegalMoveError(
            f"{attacker_state.creature.name} cannot afford {move.name} "
            f"(needs {move.fp_cost} FP, has {attacker_state.current_fp})"
        )

    spend_fp(attacker_state, move)

    hits = []

    for hit in range(move.max_hits):
        damage = resolve_hit(attacker_state, defender_state, move)
        hits.append(damage)
        if defender_state.current_lp <= 0:
            break

    secondary_result = apply_secondary_effect(attacker_state, defender_state, move)

    link_hits = []

    if defender_state.current_lp > 0:
        for ally_state, link_move in trigger_link_roll(attacker_state):
            if defender_state.current_lp <= 0:
                break
            link_hits.append((ally_state, resolve_hit(ally_state, defender_state, link_move)))

    return {"hits": hits, "secondary_effect": secondary_result, "link_hits": link_hits}


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

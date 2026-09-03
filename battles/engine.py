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

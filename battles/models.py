from django.db import models


class Creature(models.Model):
    class Element(models.TextChoices):
        FIRE = "FIRE", "Fire"
        WATER = "WATER", "Water"
        EARTH = "EARTH", "Earth"
        AIR = "AIR", "Air"
        NEUTRAL = "NEUTRAL", "Neutral"
        LEGENDARY = "LEGENDARY", "Legendary"

    class Class(models.TextChoices):
        ALL_AROUND = "ALL_AROUND", "All-Around"
        ATTACK = "ATTACK", "Attack"
        DEFENSE = "DEFENSE", "Defense"
        LONG_RANGE = "LONG_RANGE", "Long-Range"
        SUPPORT = "SUPPORT", "Support"
        TRANSFORMATION = "TRANSFORMATION", "Transformation"

    class Diet(models.TextChoices):
        CARNIVORE = "CARNIVORE", "Carnivore"
        HERBIVORE = "HERBIVORE", "Herbivore"
        OMNIVORE = "OMNIVORE", "Omnivore"
        PISCIVORE = "PISCIVORE", "Piscivore"

    class SizeCategory(models.TextChoices):
        SMALL = "SMALL", "Small"
        MEDIUM = "MEDIUM", "Medium"
        LARGE = "LARGE", "Large"
        TITANIC = "TITANIC", "Titanic"

    class Era(models.TextChoices):
        MESOZOIC_TRIASSIC = "MESOZOIC_TRIASSIC", "Mesozoic Triassic"
        MESOZOIC_JURASSIC = "MESOZOIC_JURASSIC", "Mesozoic Jurassic"
        MESOZOIC_CRETACEOUS = "MESOZOIC_CRETACEOUS", "Mesozoic Cretaceous"
        CENOZOIC_TERTIARY = "CENOZOIC_TERTIARY", "Cenozoic Tertiary"
        CENOZOIC_QUATERNARY = "CENOZOIC_QUATERNARY", "Cenozoic Quaternary"

    class DigSite(models.TextChoices):
        BB_BASE = "BB_BASE", "BB Base"
        BOTTOMSUP_BAY = "BOTTOMSUP_BAY", "Bottomsup Bay"
        COLDFEET_GLACIER = "COLDFEET_GLACIER", "Coldfeet Glacier"
        EXCHANGED_FOR_DP = "EXCHANGED_FOR_DP", "Exchanged for DP"
        GREENHORN_PLAINS = "GREENHORN_PLAINS", "Greenhorn Plains"
        KNOTWOOD_FOREST = "KNOTWOOD_FOREST", "Knotwood Forest"
        MEDAL_DEALER_JOE = "MEDAL_DEALER_JOE", "Medal-Dealer Joe"
        MOLES_SECRET_TUNNEL = "MOLES_SECRET_TUNNEL", "Moles' Secret Tunnel"
        MT_LAVAFLOW = "MT_LAVAFLOW", "Mt. Lavaflow"
        PARCHMENT_DESERT = "PARCHMENT_DESERT", "Parchment Desert"
        PAY_TO_DIG_SITE = "PAY_TO_DIG_SITE", "Pay-to-Dig Site"
        RIVET_RAVINE = "RIVET_RAVINE", "Rivet Ravine"
        SECRET_ISLAND = "SECRET_ISLAND", "Secret Island"

    number = models.PositiveSmallIntegerField(unique=True)
    name = models.CharField(max_length=100, unique=True)
    genus = models.CharField(max_length=100, blank=True)
    element = models.CharField(max_length=20, choices=Element.choices)
    creature_class = models.CharField(max_length=20, choices=Class.choices, verbose_name="Class")
    size_category = models.CharField(max_length=10, choices=SizeCategory.choices)
    diet = models.CharField(max_length=20, choices=Diet.choices, blank=True)
    era = models.CharField(max_length=30, choices=Era.choices, blank=True)
    dig_site = models.CharField(max_length=25, choices=DigSite.choices, blank=True)
    discovered_locations = models.ManyToManyField(
        "DiscoveredLocation", related_name="creatures", blank=True)
    team_skill_groups = models.ManyToManyField(
        "TeamSkillGroup", related_name="creatures", blank=True)

    lp = models.PositiveIntegerField()
    attack = models.PositiveIntegerField()
    defense = models.PositiveIntegerField()
    accuracy = models.PositiveIntegerField()
    evasion_speed = models.PositiveIntegerField()
    crit_rate = models.PositiveIntegerField()
    status_resistance = models.PositiveIntegerField(
        help_text="Percent chance to resist an incoming status effect.")
    sz_damage_multiplier = models.FloatField(
        help_text="Multiplier applied to this creature's Attack while in a Support Zone.")

    sprite = models.ImageField(upload_to="creatures/", blank=True, null=True)

    def __str__(self):
        return self.name


class SupportEffect(models.Model):
    class Target(models.TextChoices):
        SELF_AZ = "SELF_AZ", "Own Attack Zone"
        ENEMY_AZ = "ENEMY_AZ", "Enemy Attack Zone"

    creature = models.OneToOneField(Creature, on_delete=models.CASCADE,
                                    related_name="support_effect")
    target = models.CharField(max_length=10, choices=Target.choices)
    attack_magnitude = models.IntegerField(
        null=True, blank=True, help_text="Positive = Buff, negative = debuff. Blank = unaffected.")
    defense_magnitude = models.IntegerField(
        null=True, blank=True, help_text="Positive = Buff, negative = debuff. Blank = unaffected.")
    accuracy_magnitude = models.IntegerField(
        null=True, blank=True, help_text="Positive = Buff, negative = debuff. Blank = unaffected.")
    evasion_speed_magnitude = models.IntegerField(
        null=True, blank=True, help_text="Positive = Buff, negative = debuff. Blank = unaffected.")

    def __str__(self):
        return f"{self.creature.name}'s Support Effect ({self.get_target_display()})"


class Move(models.Model):
    creature = models.ForeignKey(Creature, on_delete=models.CASCADE, related_name="moveset")
    slot = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text="Skill slot order (1-4). Blank for a Team Skill.")

    name = models.CharField(max_length=100)
    damage = models.PositiveIntegerField(null=True, blank=True)
    fp_cost = models.PositiveIntegerField()
    effect = models.CharField(max_length=200, blank=True)
    effect_success_rate = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Percent change(0-100) the effect triggers. Blank if there's no effect."
    )
    counterable = models.BooleanField(default=False)
    is_team_skill = models.BooleanField(default=False, verbose_name="Team Skill")

    class Meta:
        unique_together = [("creature", "slot"), ("creature", "name")]
        ordering = ["creature", "slot"]

    def __str__(self):
        return f"{self.creature.name} slot {self.slot}: {self.name}"


class DiscoveredLocation(models.Model):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name


class TeamSkillGroup(models.Model):
    number = models.PositiveSmallIntegerField(unique=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.number} - {self.name}"


class PassiveSkill(models.Model):
    creature = models.OneToOneField(Creature, on_delete=models.CASCADE,
                                    related_name="passive_skill")
    name = models.CharField(max_length=100)
    effect = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.creature.name}'s Passive Skill: {self.name}"

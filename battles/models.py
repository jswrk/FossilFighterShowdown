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

    class SizeCategory(models.TextChoices):
        SMALL = "SMALL", "Small"
        MEDIUM = "MEDIUM", "Medium"
        LARGE = "LARGE", "Large"

    name = models.CharField(max_length=100, unique=True)
    element = models.CharField(max_length=20, choices=Element.choices)
    genus = models.CharField(max_length=100, blank=True)
    group = models.CharField(max_length=50, blank=True)
    era = models.CharField(max_length=100, blank=True)
    length_ft = models.FloatField(null=True, blank=True)
    length_m = models.FloatField(null=True, blank=True)
    size_category = models.CharField(max_length=10, choices=SizeCategory.choices)
    diet = models.CharField(max_length=20, choices=Diet.choices)
    discovered_location = models.CharField(max_length=100, blank=True)
    creature_class = models.CharField(max_length=20, choices=Class.choices, verbose_name="Class")

    lp = models.PositiveIntegerField()
    attack = models.PositiveIntegerField()
    defense = models.PositiveIntegerField()
    accuracy = models.PositiveIntegerField()
    evasion_speed = models.PositiveIntegerField()
    crit_rate = models.PositiveIntegerField()

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

    def __str__(self):
        return f"{self.creature.name}'s Support Effect ({self.get_target_display()})"


class SupportEffectStat(models.Model):
    class Stat(models.TextChoices):
        ATTACK = "ATTACK", "Attack"
        DEFENSE = "DEFENSE", "Defense"
        ACCURACY = "ACCURACY", "Accuracy"
        EVASION_SPEED = "EVASION_SPEED", "Evasion/Speed"

    support_effect = models.ForeignKey(SupportEffect, on_delete=models.CASCADE,
                                       related_name="stat_modifiers")
    stat = models.CharField(max_length=20, choices=Stat.choices)
    magnitude = models.IntegerField(help_text="Positive = buff, negative = debuff.")

    class Meta:
        unique_together = [("support_effect", "stat")]

    def __str__(self):
        return f"{self.get_stat_display()} {self.magnitude:+d}"


class Move(models.Model):
    creature = models.ForeignKey(Creature, on_delete=models.CASCADE, related_name="moveset")
    slot = models.PositiveSmallIntegerField(help_text="Skill slot order (1-4).")

    name = models.CharField(max_length=100)
    damage = models.PositiveIntegerField(null=True, blank=True)
    fp_cost = models.PositiveIntegerField()
    effect = models.CharField(max_length=200, blank=True)
    effect_success_rate = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Percent change(0-100) the effect triggers. Blank if there's no effect."
    )
    counterable = models.BooleanField(default=False)

    class Meta:
        unique_together = [("creature", "slot"), ("creature", "name")]
        ordering = ["creature", "slot"]

    def __str__(self):
        return f"{self.creature.name} slot {self.slot}: {self.name}"


class TeamSkill(models.Model):
    class TraitCategory(models.TextChoices):
        ELEMENT = "ELEMENT", "Element"
        DIET = "DIET", "Diet"
        LOCATION = "LOCATION", "Location"
        ERA = "ERA", "Era"

    creature = models.OneToOneField(Creature, on_delete=models.CASCADE, related_name="team_skill")
    name = models.CharField(max_length=100)
    damage = models.PositiveIntegerField(null=True, blank=True)
    fp_cost = models.PositiveIntegerField()
    trait_category = models.CharField(max_length=10, choices=TraitCategory.choices)
    trait_value = models.CharField(
        max_length=100,
        help_text="This specific value required across the whole team, e.g. 'Fire' or 'Carnivore'.",
    )

    def __str__(self):
        return f"{self.creature.name}'s Team Skill: {self.name}"


class PassiveSkill(models.Model):
    creature = models.OneToOneField(Creature, on_delete=models.CASCADE,
                                    related_name="passive_skill")
    name = models.CharField(max_length=100)
    effect = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.creature.name}'s Passive Skill: {self.name}"

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
import random
import string


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
        constraints = [
            models.UniqueConstraint(
                fields=["creature"],
                condition=models.Q(is_team_skill=True),
                name="unique_team_skill_per_creature",
            )
        ]

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
    class Name(models.TextChoices):
        AUTO_COUNTER = "AUTO_COUNTER", "Auto Counter"
        AUTO_LP_RECOVERY = "AUTO_LP_RECOVERY", "Auto LP Recovery"
        FP_PLUS = "FP_PLUS", "FP Plus"
        PARTING_BLOW = "PARTING_BLOW", "Parting Blow"
        ZERO_SUPPORT = "ZERO_SUPPORT", "Zero Support"

    creature = models.OneToOneField(Creature, on_delete=models.CASCADE,
                                    related_name="passive_skill")
    name = models.CharField(max_length=20, choices=Name.choices)
    effect = models.CharField(max_length=200, blank=True)

    # parting blow
    attack_percent = models.IntegerField(null=True, blank=True)
    defense_percent = models.IntegerField(null=True, blank=True)
    accuracy_percent = models.IntegerField(null=True, blank=True)
    evasion_speed_percent = models.IntegerField(null=True, blank=True)

    # auto lp recovery
    lp_recovery_percent = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.creature.name}'s Passive Skill: {self.name}"


class PlayerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="profile")
    display_name = models.CharField(max_length=50, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    favorite_creature = models.ForeignKey(
        Creature, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="favorited_by"
    )
    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)

    @property
    def win_rate(self):
        total = self.wins + self.losses
        return round(self.wins / total * 100, 1) if total else 0.0

    def __str__(self):
        return self.display_name or self.user.username


class Team(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name="teams")
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.owner.username})"


class TeamSlot(models.Model):
    class Role(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        RESERVE = "RESERVE", "Reserve"

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="slots")
    creature = models.ForeignKey(Creature, on_delete=models.CASCADE, related_name="team_slots")
    role = models.CharField(max_length=8, choices=Role.choices)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ["team", "role", "order"]
        constraints = [
            models.UniqueConstraint(fields=["team", "creature"],
                                    name="unique_creature_per_team"),
            models.UniqueConstraint(fields=["team", "role", "order"],
                                    name="unique_slot_order_per_team_role"),
        ]

    def clean(self):
        if self.team_id is None:
            return
        limits = {"ACTIVE": 3, "RESERVE": 2}
        existing = TeamSlot.objects.filter(team=self.team,
                                           role=self.role).exclude(pk=self.pk).count()
        if existing >= limits[self.role]:
            raise ValidationError(
                f"A team can have at most {limits[self.role]} {self.role.lower()} creatures.")


ROOM_CODE_CHARS = string.ascii_uppercase + string.digits


def generate_room_code():
    return "".join(random.choices(ROOM_CODE_CHARS, k=6))


class BattleRoom(models.Model):
    class Status(models.TextChoices):
        WAITING = "WAITING", "Waiting"
        ACTIVE = "ACTIVE", "Active"
        FINISHED = "FINISHED", "Finished"

    host = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, related_name="hosted_rooms")
    guest = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              null=True, blank=True, related_name="joined_rooms")
    host_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="hosted_rooms")
    guest_team = models.ForeignKey(Team, on_delete=models.CASCADE,
                                   null=True, blank=True, related_name="guested_rooms")
    room_code = models.CharField(max_length=6, unique=True)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.WAITING)
    winner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                               null=True, blank=True, related_name="won_rooms")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        guest_name = self.guest.username if self.guest else "waiting"
        return f"{self.room_code}: {self.host.username} vs {guest_name}"

    def save(self, *args, **kwargs):
        if not self.room_code:
            code = generate_room_code()
            while BattleRoom.objects.filter(room_code=code).exists():
                code = generate_room_code()
            self.room_code = code
        super().save(*args, **kwargs)

    def finish(self, winner):
        if winner not in (self.host, self.guest):
            raise ValidationError("Winner must be the host or guest of this room.")

        loser = self.guest if winner == self.host else self.host

        self.winner = winner
        self.status = self.Status.FINISHED
        self.save()

        winner.profile.wins += 1
        winner.profile.save()
        loser.profile.losses += 1
        loser.profile.save()


class BattleState(models.Model):
    room = models.OneToOneField(BattleRoom, on_delete=models.CASCADE, related_name="state")
    host_ez_turns_left = models.PositiveSmallIntegerField(null=True, blank=True)
    guest_ez_turns_left = models.PositiveSmallIntegerField(null=True, blank=True)


class BattleCreatureState(models.Model):
    class Side(models.TextChoices):
        HOST = "HOST", "Host"
        GUEST = "GUEST", "Guest"

    class Zone(models.TextChoices):
        AZ = "AZ", "Attack Zone"
        SZ1 = "SZ1", "Support Zone One"
        SZ2 = "SZ2", "Support Zone Two"
        EZ = "EZ", "Escape Zone"
    battle_state = models.ForeignKey(
        BattleState, on_delete=models.CASCADE, related_name="creature_states")
    creature = models.ForeignKey(Creature, on_delete=models.CASCADE)
    side = models.CharField(max_length=5, choices=Side.choices)
    zone = models.CharField(max_length=20, choices=Zone.choices)
    current_lp = models.PositiveIntegerField()
    current_fp = models.PositiveIntegerField()
    status_effect = models.CharField(max_length=100, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["battle_state", "side", "zone"],
                                    name="unique_zone_per_side"),
        ]

from django.contrib.auth import get_user_model
from django.test import TestCase

from . import engine
from .models import (BattleCreatureState, BattleRoom, BattleState,
                     Creature, Move, PassiveSkill, Team)

HOST = BattleCreatureState.Side.HOST
GUEST = BattleCreatureState.Side.GUEST
Zone = BattleCreatureState.Zone


def make_creature(number, name, lp=300):
    return Creature.objects.create(
        number=number, name=name, element=Creature.Element.NEUTRAL,
        creature_class=Creature.Class.ALL_AROUND, size_category=Creature.SizeCategory.MEDIUM,
        lp=lp, attack=50, defense=20, accuracy=50, evasion_speed=50, crit_rate=0,
        status_resistance=0, sz_damage_multiplier=1.0,
    )


class FPTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user("tester", password="x")
        cls.team = Team.objects.create(owner=cls.user, name="Test Team")

        cls.attacker = make_creature(1, "Attacker")
        cls.ally = make_creature(2, "Ally")
        cls.defender = make_creature(3, "Defender", lp=100000)

        cls.big_move = Move.objects.create(
            creature=cls.attacker, slot=1, name="Big Move", damage=10, fp_cost=120)
        cls.link_move = Move.objects.create(
            creature=cls.ally, slot=1, name="Link Move", damage=10, fp_cost=30,
            is_link_skill=True, link_chance_percent=100
        )

    def setUp(self):
        room = BattleRoom.objects.create(host=self.user, host_team=self.team)
        self.bs = BattleState.objects.create(room=room)
        self.az = self._place(self.attacker, HOST, Zone.AZ)
        self.sz = self._place(self.ally, HOST, Zone.SZ1)
        self.foe = self._place(self.defender, GUEST, Zone.AZ)

    def _place(self, creature, side, zone):
        state = BattleCreatureState.objects.create(
            battle_state=self.bs, creature=creature, side=side, zone=zone,
            current_lp=creature.lp
        )
        return BattleCreatureState.objects.get(pk=state.pk)

    def _pool(self, side):
        return getattr(BattleState.objects.get(pk=self.bs.pk), f"{side.lower()}_fp")


class FPPoolHelperTests(FPTestBase):
    def test_battle_starts_at_zero_fp(self):
        self.assertEqual(self._pool(HOST), 0)
        self.assertEqual(self._pool(GUEST), 0)

    def test_set_clamps_between_zero_and_max(self):
        self.assertEqual(engine._set_fp_pool(self.bs, HOST, -50), 0)
        self.assertEqual(engine._set_fp_pool(self.bs, HOST, 900), engine.MAX_FP)
        self.assertEqual(self._pool(HOST), engine.MAX_FP)

    def test_get_refreshes_stale_copy(self):
        copy_a = BattleState.objects.get(pk=self.bs.pk)
        copy_b = BattleState.objects.get(pk=self.bs.pk)
        engine._set_fp_pool(copy_a, HOST, 80)
        self.assertEqual(engine._get_fp_pool(copy_b, HOST), 80)

    def test_set_only_writes_its_own_side(self):
        engine._set_fp_pool(self.bs, HOST, 500)
        stale = BattleState.objects.get(pk=self.bs.pk)
        stale.host_fp = 1
        engine._set_fp_pool(stale, GUEST, 60)
        self.assertEqual(self._pool(HOST), 500)
        self.assertEqual(self._pool(GUEST), 60)


class SpendFPTests(FPTestBase):
    def setUp(self):
        super().setUp()
        engine._set_fp_pool(self.bs, HOST, 200)
        engine._set_fp_pool(self.bs, GUEST, 150)

    def test_is_move_legal_reads_side_pool(self):
        self.assertTrue(engine.is_move_legal(self.az, self.big_move))
        engine._set_fp_pool(self.bs, HOST, 100)
        self.assertFalse(engine.is_move_legal(self.az, self.big_move))

    def test_spend_fp_deducts_from_own_side_only(self):
        engine.spend_fp(self.az, self.big_move)
        self.assertEqual(self._pool(HOST), 80)
        self.assertEqual(self._pool(GUEST), 150)

    def test_sz_sees_az_spend_despite_stale_cope(self):
        self.assertEqual(self.sz.battle_state.host_fp, 200)
        engine.spend_fp(self.az, self.big_move)
        self.assertFalse(engine.is_move_legal(self.sz, self.big_move))

    def test_execute_move_spends_once_and_link_is_free(self):
        result = engine.execute_move(self.az, self.foe, self.big_move)
        self.assertEqual(len(result["link_hits"]), 1)
        self.assertEqual(self._pool(HOST), 80)

    def test_illegal_move_raises_without_spending(self):
        engine._set_fp_pool(self.bs, HOST, 100)
        with self.assertRaises(engine.IllegalMoveError):
            engine.execute_move(self.az, self.foe, self.big_move)
        self.foe.refresh_from_db()
        self.assertEqual(self._pool(HOST), 100)
        self.assertEqual(self.foe.current_lp, self.defender.lp)


class RechargeFPTests(FPTestBase):
    def _give_passive(self, creature, name, fp_plus_percent=None):
        PassiveSkill.objects.create(creature=creature, name=name,
                                    fp_plus_percent=fp_plus_percent)

    def test_recharge_without_fp_plus(self):
        self.assertEqual(engine.recharge_fp(self.bs, HOST), engine.FP_RECHARGE)
        self.assertEqual(self._pool(HOST), engine.FP_RECHARGE)

    def test_recharge_only_touches_own_side(self):
        engine.recharge_fp(self.bs, GUEST)
        self.assertEqual(self._pool(HOST), 0)

    def test_non_fp_plus_passive_ignored(self):
        self._give_passive(self.defender, PassiveSkill.Name.AUTO_COUNTER)
        self.assertEqual(engine.recharge_fp(self.bs, GUEST), 180)

    def test_fp_plus_stacks_additively(self):
        self._give_passive(self.attacker, PassiveSkill.Name.FP_PLUS, 20)
        self._give_passive(self.ally, PassiveSkill.Name.FP_PLUS, 10)
        self.assertEqual(engine.recharge_fp(self.bs, HOST), 234)

    def test_knocked_out_holder_excluded(self):
        self._give_passive(self.attacker, PassiveSkill.Name.FP_PLUS, 20)
        self._give_passive(self.ally, PassiveSkill.Name.FP_PLUS, 10)
        self.az.current_lp = 0
        self.az.save()
        self.assertEqual(engine.recharge_fp(self.bs, HOST), 198)

    def test_holder_in_ez_still_counts(self):
        self._give_passive(self.attacker, PassiveSkill.Name.FP_PLUS, 20)
        self.az.zone = Zone.EZ
        self.az.save()
        self.assertEqual(engine.recharge_fp(self.bs, HOST), 216)

    def test_recharge_caps_at_max_and_returns_actual_gain(self):
        engine._set_fp_pool(self.bs, HOST, 400)
        self.assertEqual(engine.recharge_fp(self.bs, HOST), 100)
        self.assertEqual(self._pool(HOST), engine.MAX_FP)
        self.assertEqual(engine.recharge_fp(self.bs, HOST), 0)

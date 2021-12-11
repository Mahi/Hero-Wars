from filters.weapons import WeaponClassIter
from listeners.tick import Delay, Repeat
from mathlib import Vector


class TraditionalTools:

    def player_spawn(player, **rest):
        player.restrict_weapons(*(
            weapon.name
            for weapon in WeaponClassIter()
            if weapon.name not in ('weapon_knife', 'weapon_c4')
        ))


class SharpBlade:

    def pre_player_attack(skill, take_damage_info, **rest):
        multiplier = 1 + skill.current('damage') / 100
        take_damage_info.damage *= multiplier


class Leap:

    def player_spawn(skill, player, **rest):
        skill.chat(player, 'spawn_message', longjump=skill.current('longjump'))

    def player_jump(skill, player, **rest):
        boost = 1 + skill.current('longjump') / 100
        player.base_velocity = Vector(
            min(player.velocity.x * boost, 1000),
            min(player.velocity.y * boost, 1000),
            player.velocity.z,
        )


class Meditation:

    def init(player, hero, skill):
        skill._repeat = Repeat(Meditation._tick)

    def _tick(player, skill):
        player.health = min(player.health + skill.current('heal'), player.max_health)
        if player.health == player.max_health:
            skill._repeat.stop()

    def player_victim(skill, player, **rest):
        skill._repeat.args = (player, skill)
        skill._repeat.start(skill.current('interval'))

    def skill_upgrade(skill, **rest):
        skill._repeat.stop()
        skill._repeat.start(skill.current('interval'))

    skill_downgrade = skill_upgrade


class TotalVanish:

    def init(player, hero, skill):
        skill._paralyze = None

    def player_ultimate(skill, player, **rest):
        if skill._paralyze is None:
            if skill.cooldown() <= 0:
                player.color = player.color.with_alpha(0)
                skill._paralyze = player.paralyze()
                Delay(skill.current('duration'), TotalVanish._cancel, (skill, player))
                for weapon in player.weapons():
                    weapon.remove()

        else:
            TotalVanish._cancel(skill, player)

    def _cancel(skill, player):
        if skill._paralyze is not None:
            skill._paralyze.cancel()
            skill._paralyze = None
            player.color = player.color.with_alpha(255)
            player.give_named_item('weapon_knife')
            skill.cooldown()
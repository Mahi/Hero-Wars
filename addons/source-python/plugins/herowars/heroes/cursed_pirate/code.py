from enum import Enum

from listeners.tick import Delay
from colors import Color, RED

from herowars.utils import chance


class Plunder:

    def player_attack(skill, player, victim, dmg_health, **rest):
        if chance(skill.current('chance')):
            money = min(victim.cash, skill.current('money'))
            victim.cash -= money
            player.cash += money

            health = int(dmg_health * skill.current('lifesteal') // 100)
            player.health += health

            skill.effect('beam', start_point=player.eye_location, end_point=victim.chest_location)
            skill.send_string(player, 'attacker_message', money=money, health=health)
            skill.send_string(victim, 'victim_message', money=money)


class RaiseTheSails:
    
    def player_spawn(skill, player, **rest):
        player.speed += skill.current('speed') / 100
        skill.send_string(player, 'message', speed=skill.current('speed'))


class Loot:

    def player_spawn(skill, player, **rest):
        items = {
            'hegrenade': False,
            'flashbang': False,
            'smokegrenade': False,
            'molotov': False,
        }
        for item in items.keys():
            if chance(skill.current(f'{item}_chance')):
                items[item] = True
                player.give_named_item(f'weapon_{item}')
        if any(items.values()):
            skill.send_string(player, 'message', items=', '.join(item for item, give in items.items() if give))


class _FinalCursePhase(Enum):
    WAITING = 0
    CURSED = 1
    SAVED = 2


class FinalCurse:
    
    def init(player, hero, skill):
        skill._phase = _FinalCursePhase.WAITING

    def player_spawn(skill, **rest):
        skill._phase = _FinalCursePhase.WAITING

    def pre_player_victim(skill, player, attacker, take_damage_info, **rest):
        if skill._phase == _FinalCursePhase.WAITING and take_damage_info.damage >= player.health:
            skill._phase = _FinalCursePhase.CURSED
            take_damage_info.damage = 0
            player.health = 1
            godmode = player.godmode()
            player.color = Color(255, 150, 150)
            Delay(skill.current('duration'), FinalCurse._end_curse, (player, attacker.index, skill, godmode))

            skill.effect('ring', center=player.stomach_location)
            player.display(
                skill.strings['start_hud_message'],
                message_kwargs={'color1': RED, 'y': 0.5},
            )

    def player_kill(player, skill, **eargs):
        if skill._phase == _FinalCursePhase.CURSED:
            skill._phase = _FinalCursePhase.SAVED
            player.color = Color(255, 255, 255)
            skill.send_string(player, 'success_message')

    def _end_curse(player, attacker_index, skill, godmode):
        godmode.cancel()
        if skill._phase == _FinalCursePhase.CURSED:
            player.color = Color(255, 255, 255)
            player.take_damage(player.health + 999, attacker_index=attacker_index, skip_hooks=True)
            skill.send_string(player, 'fail_message')

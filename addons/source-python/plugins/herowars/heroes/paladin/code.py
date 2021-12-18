from colors import Color
from filters.players import PlayerIter
from listeners.tick import Delay

from herowars.utils import chance


class Condemn:

    def player_attack(skill, player, victim, **rest):
        if chance(skill.current('chance')):
            duration = skill.current('duration')
            victim.freeze(duration)
            skill.send_string(victim, 'victim_message', duration=duration)
            skill.effect('beam', start_point=player.hip_location, end_point=victim.hip_location, life_time=duration)
            skill.effect('freeze', start_point=victim.origin, end_point=victim.eye_location, life_time=duration)


class SaintsCloak:

    def player_spawn(skill, player, **rest):
        player.max_health += skill.current('health')
        player.health += skill.current('health')

        alpha = 255 * (1 - skill.current('invis') / 100)
        player.color = player.color.with_alpha(int(alpha))


class Martyr:

    def player_death(skill, player, attacker, **rest):
        damage = int(skill.current('damage'))
        heal = skill.current('heal')

        for player in PlayerIter(is_filters=[player.cs_team]):
            player.health += heal
            skill.send_string(player, 'teammate_message', heal=heal)

        attacker.take_damage(skill.current('damage'), attacker_index=player.index)
        skill.send_string(player, 'user_message', heal=heal, name=attacker.name, damage=damage)
        skill.send_string(attacker, 'killer_message', name=player.name, damage=damage)


class GodMode:

    def player_ultimate(skill, player, **rest):
        if skill.cooldown() <= 0:
            duration = skill.current('duration')
            player.godmode(duration)
            skill.send_string(player, 'start_message', duration=duration)
            old_color = player.color
            player.color = Color(255, 255, 0)
            Delay(duration, GodMode._end_ultimate, (skill, player, old_color))

    def _end_ultimate(skill, player, color):
        player.color = color
        skill.send_string(player, 'end_message')

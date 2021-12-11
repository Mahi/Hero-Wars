from filters.weapons import WeaponClassIter


class HeavyWeaponry:

    def player_spawn(skill, player, **eargs):
        player.speed *= 1 - skill.current('slow') / 100
        player.restrict_weapons(*(
            weapon.name
            for weapon in WeaponClassIter()
            if weapon.name not in ('weapon_knife', 'weapon_deagle', 'weapon_m249', 'weapon_c4')
        ))
        skill.chat(player, 'message', slow=skill.current('slow'))
        player.give_named_item('weapon_deagle')


class TitaniumBullets:

    def pre_player_attack(skill, player, take_damage_info, **eargs):
        damage = int(take_damage_info.damage * (1 + skill.current('damage') / 100))
        take_damage_info.damage += damage
        skill.chat(player, 'message', damage=damage)


class SteelArmor:

    def init(player, hero, skill):
        skill._hit_count = 0

    def player_spawn(skill, player, **eargs):
        player.max_health += skill.current('health')
        player.health += skill.current('health')
        skill.chat(player, 'spawn_message', health=skill.current('health'))
    
    def pre_player_victim(skill, player, take_damage_info, **eargs):
        if skill._hit_count < skill.current('blocks'):
            skill._hit_count += 1
        else:
            skill.chat(player, 'block_message', damage=int(take_damage_info.damage))
            take_damage_info.damage = 0
            skill._hit_count = 0


class RocketBoosters:

    def init(player, hero, skill):
        skill._fly = None

    def player_death(skill, **eargs):
        if skill._fly is not None:
            skill._fly.cancel()
            skill._fly = None
    
    def player_ultimate(skill, player, **eargs):
        if skill._fly is None:
            if skill.cooldown() <= 0:
                skill._fly = player.fly()
                skill.cooldown('off_cooldown')
                skill.chat(player, 'description')
        elif skill.cooldown('off_cooldown') <= 0:
            skill._fly.cancel()
            skill._fly = None
            skill.cooldown()
            skill.chat(player, 'end_message')

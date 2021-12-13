
# Source-Python imports
from commands import CommandReturn
from commands.client import ClientCommand
from commands.say import SayCommand
from entities import TakeDamageInfo
from entities.helpers import index_from_pointer
from entities.hooks import EntityCondition
from entities.hooks import EntityPreHook
from events import Event
from memory import make_object
from messages.colors.saytext2 import GREEN, WHITE

# Hero-Wars imports
from . import database, menus, strings
from .constants import DUO_PLAYER_EVENTS, SOLO_PLAYER_EVENTS, XP_ON_KILL
from .listeners import OnHeroLevelUp, OnPlayerChangeHero
from .players import player_dict


# Invoke hero and skill callbacks

@Event(*SOLO_PLAYER_EVENTS)
def _on_solo_player_event(game_event):
    event_args = game_event.variables.as_dict()
    player = player_dict.from_userid(event_args.pop('userid'))
    player.invoke_callbacks(game_event.name, event_args)


@Event(*DUO_PLAYER_EVENTS.keys())
def _on_duo_player_event(game_event):
    event_args = game_event.variables.as_dict()
    try:
        attacker = player_dict.from_userid(event_args.pop('attacker'))
    except KeyError:
        attacker = None
    victim = player_dict.from_userid(event_args.pop('userid'))
    event_args.update(attacker=attacker, victim=victim)
    victim_event, attacker_event = DUO_PLAYER_EVENTS[game_event.name]
    victim.invoke_callbacks(victim_event, event_args)
    if attacker is not None:
        attacker.invoke_callbacks(attacker_event, event_args)


@EntityPreHook(EntityCondition.is_player, 'on_take_damage')
def _invoke_pre_damage_callbacks(args):
    take_damage_info = make_object(TakeDamageInfo, args[1])
    if not take_damage_info.attacker:
        return
    attacker = player_dict[take_damage_info.attacker]
    victim = player_dict[index_from_pointer(args[0])]
    if victim.team == attacker.team:
        return
    event_args = {
        'attacker': attacker,
        'victim': victim,
        'take_damage_info': take_damage_info,
    }
    attacker.invoke_callbacks('pre_player_attack', event_args)
    victim.invoke_callbacks('pre_player_victim', event_args)


@ClientCommand('+ultimate')
def _cmd_ultimate(command, player_index):
    player = player_dict[player_index]
    player.invoke_callbacks('player_ultimate', {})


@ClientCommand('-ultimate')
def _cmd_ultimate(command, player_index):
    player = player_dict[player_index]
    player.invoke_callbacks('player_ultimate_end', {})


@ClientCommand('+ability')
def _cmd_ability(command, player_index):
    player = player_dict[player_index]
    player.invoke_callbacks('player_ability', {})


@ClientCommand('-ability')
def _cmd_ability(command, player_index):
    player = player_dict[player_index]
    player.invoke_callbacks('player_ability_end', {})


# Custom commands

@ClientCommand('hw_menu')
@SayCommand(('!hw', '!herowars'))
def _cmd_herowars_menu(command, player_index, team_only=None):
    menus.main.send(player_index)


@ClientCommand('hw_heroinfo')
@SayCommand('!heroinfo')
def _cmd_heroinfo(command, player_index, team_only=None):
    player = player_dict[player_index]
    hero = player.hero
    player.chat(
        strings.hero_info,
        name=hero.name,
        level=hero.level,
        xp=hero.xp,
        required_xp=hero.required_xp,
    )
    return CommandReturn.BLOCK


@ClientCommand('hw_resetskills')
@SayCommand('!resetskills')
def _cmd_resetskills(command, player_index, team_only=None):
    player = player_dict[player_index]
    player.hero.reset_skills()
    player.chat(
        strings.unspent_skill_points,
        hero_name=player.hero.name,
        skill_points=player.hero.skill_points
    )
    menus.upgrade_skills.send(player_index)
    return CommandReturn.BLOCK


@OnPlayerChangeHero
def _on_hero_change(player, **event_args):
    if not player.dead:
        player.slay()

    event_args['new_hero']._create_skills()
    database.load_skills_data(event_args['new_hero'])
    player.invoke_init_callbacks()
    player.invoke_callbacks('player_change_hero', event_args)

    database.save_hero_data(event_args['old_hero'])
    event_args['old_hero'].skills.clear()

    player.chat(strings.change_hero, hero_name=player.hero.name)


@OnHeroLevelUp
def _on_hero_level_up(player, **event_args):
    player.invoke_callbacks('hero_level_up', event_args)
    hero = player.hero
    player.chat(
        strings.hero_info,
        name=hero.name,
        level=hero.level,
        xp=hero.xp,
        required_xp=hero.required_xp,
    )


@Event('player_spawn')
def _on_spawn(event):
    player = player_dict.from_userid(event['userid'])
    hero = player.hero
    player.chat(
        strings.hero_info,
        name=hero.name,
        level=hero.level,
        xp=hero.xp,
        required_xp=hero.required_xp,
    )


@Event('player_death')
def _on_death(event):
    victim = player_dict.from_userid(event['userid'])
    database.save_player_data(victim)

    try:
        attacker = player_dict.from_userid(event['attacker'])
    except KeyError:
        return
    old_level = attacker.hero.level
    attacker.hero.xp += XP_ON_KILL
    attacker.chat(
        strings.messages['Kill XP'],
        color=GREEN,
        white=WHITE,
        xp=XP_ON_KILL,
    )
    if attacker.hero.level > old_level:
        OnHeroLevelUp.manager.notify(
            player=attacker,
            hero=attacker.hero,
            old_level=old_level,
            new_level=attacker.hero.level,
        )


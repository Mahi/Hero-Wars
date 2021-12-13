
# Source-Python imports
from commands import CommandReturn
from commands.client import ClientCommand
from commands.say import SayCommand
from messages.colors.saytext2 import GREEN, WHITE

# Hero-Wars imports
from . import database, menus, strings
from .constants import CUSTOM_PLAYER_EVENTS, XP_ON_KILL
from .events import events
from .players import player_dict


# Messages and data management

@events.on('player_change_hero')
def _on_player_change_hero(player, new_hero, old_hero, **eargs):
    if not player.dead:
        player.slay()

    database.save_hero_data(old_hero)
    old_hero.skills.clear()

    new_hero._create_skills()
    database.load_skills_data(new_hero)
    player.invoke_init_callbacks()

    player.chat(strings.change_hero, hero_name=player.hero.name)


@events.on('hero_level_up')
def _on_hero_level_up(player, hero, **eargs):
    player.chat(
        strings.hero_info,
        name=hero.name,
        level=hero.level,
        xp=hero.xp,
        required_xp=hero.required_xp,
    )


@events.on('player_spawn')
def _on_player_spawn(player, **eargs):
    hero = player.hero
    player.chat(
        strings.hero_info,
        name=hero.name,
        level=hero.level,
        xp=hero.xp,
        required_xp=hero.required_xp,
    )


@events.on('player_death')
def _on_death(victim, attacker, **eargs):
    database.save_player_data(victim)

    if attacker is None:
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
        events['hero_level_up'].fire(
            player=attacker,
            hero=attacker.hero,
            old_level=old_level,
            new_level=attacker.hero.level,
        )


# Menu and operation commands

@ClientCommand('hw_menu')
@SayCommand(('!hw', '!herowars'))
def _cmd_herowars_menu(command, player_index, team_only=None):
    menus.main.send(player_index)
    return CommandReturn.BLOCK


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


# Invoke hero and skill callbacks
# This should stay at the bottom to ensure being called last

@events.on(
    'player_jump', 'player_spawn', 'player_kill', 'player_death', 'player_attack', 'player_victim',
    *CUSTOM_PLAYER_EVENTS,
    named=True,
)
def _invoke_callbacks(event_name, player, **eargs):
    player.invoke_callbacks(event_name, eargs)

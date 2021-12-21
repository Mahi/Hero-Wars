# Python imports
import functools

# Source-Python imports
from commands import CommandReturn
from commands.client import ClientCommand
from commands.say import SayCommand
from cvars import ConVar
from messages.colors.saytext2 import GREEN, WHITE
from plugins.info import PluginInfo


# Hero-Wars imports
from . import config, database, menus, strings
from .events import events
from .players import player_dict
from .utils import create_translation_string


plugin_info = PluginInfo(
    name='herowars',
    verbose_name='Hero-Wars',
    author='Mahi',
    version='2.0.0_alpha',
    url='https://gitlab.com/Mahi/Hero-Wars',
)
ConVar('hw_version', plugin_info.version)


# Messages and data management

def unload():
    for player in player_dict.values():
        database.save_player_data(player)


@events.on(*config.xp_for_event.keys(), named=True)
def _give_xp(event_name, player, **eargs):
    amount = config.xp_for_event[event_name].get_int()
    old_level = player.hero.level
    player.hero.xp += amount
    if player.hero.level > old_level:
        events['hero_level_up'].fire(
            player=player,
            hero=player.hero,
            old_level=old_level,
            new_level=player.hero.level,
        )
    player.chat(create_translation_string(
        f'{GREEN}+{amount} {{xp_string}}{WHITE}: {{event_string}}',
        xp_string=strings.common['XP'],
        event_string=strings.messages[event_name],
    ))


@events.on('player_change_hero')
def _on_player_change_hero(player, new_hero, old_hero, **eargs):
    database.save_hero_data(old_hero)
    old_hero.skills.clear()

    new_hero._create_skills()
    if new_hero._db_id is None:
        database.create_hero_data(new_hero, player.steamid)
    else:
        database.load_skills_data(new_hero)
    player.invoke_init_callbacks()

    if not player.dead:
        player.slay()

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
def _on_death(victim, **eargs):
    database.save_player_data(victim)
    if victim.hero.skill_points > 0 and any(skill.level < skill.max_level for skill in victim.hero.skills):
        menus.upgrade_skills.send(victim.index)


# Menus and commands

def _cmd_resetskills(player_index):
    player = player_dict[player_index]
    player.hero.reset_skills()
    player.chat(
        strings.unspent_skill_points,
        hero_name=player.hero.name,
        skill_points=player.hero.skill_points
    )
    menus.upgrade_skills.send(player_index)


def _cmd_heroinfo(player_index):
    player = player_dict[player_index]
    hero = player.hero
    player.chat(
        strings.hero_info,
        name=hero.name,
        level=hero.level,
        xp=hero.xp,
        required_xp=hero.required_xp,
    )


_commands = (
    # (clientcommand, (saycommands,), callback),
    ('hw_menu', ('!hw', '!herowars'), menus.main.send),
    ('hw_changehero', ('!ch', '!changehero'), menus.change_hero.send),
    ('hw_upgradeskills', ('!us', '!upgradeskills'), menus.upgrade_skills.send),
    ('hw_resetskills', ('!rs', '!resetskills'), _cmd_resetskills),
    ('hw_heroinfo', ('!hi', '!heroinfo'), _cmd_heroinfo),
)

def _run_command(callback, command, player_index, team_only=None):
    callback(player_index)
    return CommandReturn.BLOCK


for client_cmd, say_cmds, callback in _commands:
    _cmd = functools.partial(_run_command, callback)
    _cmd = ClientCommand(client_cmd)(_cmd)
    _cmd = SayCommand(say_cmds)(_cmd)



# Invoke hero and skill callbacks for all existing events
# This should stay at the bottom to ensure skills are being called last

@events.on(*events, named=True)
def _invoke_callbacks(event_name, player, **eargs):
    player.invoke_callbacks(event_name, eargs)

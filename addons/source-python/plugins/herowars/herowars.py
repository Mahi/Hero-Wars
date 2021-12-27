# Python imports
import functools
from typing import Callable, Optional

# Source-Python imports
from commands import Command, CommandReturn
from commands.client import ClientCommand
from commands.say import SayCommand
from cvars import ConVar
from easyevents import event
from messages.colors.saytext2 import GREEN, WHITE
from plugins.info import PluginInfo


# Hero-Wars imports
from . import config, database, menus, strings
from .entities.hero import Hero
from .events import events
from .player import Player, UpgradeSkillsPopup
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


@events.on('player_death', 'player_disconnect')
def _save_player_data(player: Player, **eargs):
    database.save_player_data(player)


@events.on('player_change_hero')
def _on_player_change_hero(player: Player, new_hero: Hero, old_hero: Hero, **eargs):
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


@events.on(*config.xp_for_event.keys(), named=True)
def _give_xp(event_name: str, player: Player, **eargs):
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


@events.on('hero_level_up', 'player_spawn')
def _send_hero_info(player: Player, **eargs):
    hero = player.hero
    player.chat(
        strings.hero_info,
        name=hero.name,
        level=hero.level,
        xp=hero.xp,
        required_xp=hero.required_xp,
    )


_UPGRADE_SKILLS_POPUP = {
    'player_death': UpgradeSkillsPopup.ON_DEATH,
    'player_suicide': UpgradeSkillsPopup.ON_DEATH,
    'hero_level_up': UpgradeSkillsPopup.ON_LEVEL_UP,
}

@events.on(*_UPGRADE_SKILLS_POPUP.keys(), named=True)
def _send_upgrade_skills_popup(event_name: str, player: Player, **eargs):
    if (
        player.settings.upgrade_skills_popup == _UPGRADE_SKILLS_POPUP[event_name]
        and player.hero.skill_points > 0
        and any(player.hero.can_upgrade_skill(skill) for skill in player.hero.skills)
    ):
        menus.upgrade_skills.send(player.index)


# Menus and commands


def _cmd_resetskills(player_index: int):
    player = player_dict[player_index]
    player.hero.reset_skills()
    player.chat(
        strings.unspent_skill_points,
        hero_name=player.hero.name,
        skill_points=player.hero.skill_points
    )
    menus.upgrade_skills.send(player_index)


def _cmd_heroinfo(player_index: int):
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

def _run_command(callback: Callable[[int], None], command: Command, player_index: int, team_only: Optional[bool]=None):
    callback(player_index)
    return CommandReturn.BLOCK


for client_cmd, say_cmds, callback in _commands:
    _cmd = functools.partial(_run_command, callback)
    _cmd = ClientCommand(client_cmd)(_cmd)
    _cmd = SayCommand(say_cmds)(_cmd)


@ClientCommand('+lookatweapon', '-lookatweapon')
def inspect_to_ult(command: Command, player_index: int):
    """Use player ultimate when they inspect their weapon."""
    player = player_dict[player_index]
    if player.settings.inspect_to_ult:
        eargs = {'player': player}
        if command.command_string == '+lookatweapon':
            event = 'player_ultimate'
        else:  # '-lookatweapon'
            event = 'player_ultimate_end'
        player.invoke_callbacks(event, eargs)
        return CommandReturn.BLOCK


# Invoke hero and skill callbacks for all existing events
# This should stay at the bottom to ensure skills are being called last

@events.on(*events, named=True)
def _invoke_callbacks(event_name: str, player: Player, **eargs):
    player.invoke_callbacks(event_name, eargs)

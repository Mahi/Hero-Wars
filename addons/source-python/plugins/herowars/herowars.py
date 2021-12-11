# Python 3 imports
from collections import defaultdict
from typing import Dict, List, Optional, Type

# Source-Python imports
from commands import Command as SpCommand, CommandReturn
from commands.client import ClientCommand, client_command_manager
from commands.say import SayCommand, say_command_manager
from entities import TakeDamageInfo
from entities.helpers import index_from_pointer
from entities.hooks import EntityCondition
from entities.hooks import EntityPreHook
from events import Event as SpEvent, GameEvent
from events.manager import event_manager
from memory import make_object
from messages.base import SayText2
from messages.colors.saytext2 import WHITE, GREEN, ORANGE
from players.dictionary import PlayerDictionary
from translations.strings import TranslationStrings

# Hero-Wars imports
from . import strings
from .builder import build_hero_types
from .constants import *
from .entities import Hero
from .entities.type_objects import HeroType
from .listeners import OnHeroLevelUp, OnPlayerChangeHero
from .plugin_state import PluginState
from .player import Player
from .systems.database import DatabaseSystem
from .systems.menus import MenuSystem
from .systems.skill_trigger import SkillTriggerSystem
from .systems.system import Command, CommandHandler, Event, EventHandler, System
from .systems.xp import XpSystem
from .utils import first


class HeroWars:

    def __init__(self, **plugin_systems):
        self.state: PluginState = PluginState(
            hero_types=build_hero_types(HEROES_PATH),
            players=PlayerDictionary(self._init_player),
        )
        self.systems: Dict[str, System] = self._init_systems({
            'db': DatabaseSystem,
            'menu': MenuSystem,
            'skill': SkillTriggerSystem,
            'xp': XpSystem,
            **plugin_systems,
        })
        self._command_handlers: Dict[str, List[CommandHandler]] = defaultdict(list)
        self._event_handlers: Dict[str, List[EventHandler]] = defaultdict(list)

    def _init_systems(self, system_classes: Dict[str, Type[System]]) -> Dict[str, System]:
        systems = {}
        for key, system_cls in system_classes.items():
            systems[key] = system_cls(state=self.state)
        return systems

    def _init_player(self, player_index: int) -> Player:
        player = Player(player_index)
        exists = self.systems['db'].load_player_data(player)
        if not player.hero:  # Prior data might still exist, just hero has been deleted
            if player.heroes:
                player.hero = first(player.heroes)
            else:
                hero = Hero(self._get_default_hero_type())
                player.heroes[hero.key] = hero
                player.hero = hero
        if not exists:
            # Pre-emptively insert into database to allow update operations 
            # in the future, without having to query for existance every time
            self.systems['db'].create_player_data(player)
            player.chat(strings.welcome)
        player._init_hero()
        return player
        
    def _get_default_hero_type(self) -> HeroType:
        if DEFAULT_HERO_KEY is None:
            return first(self.state.hero_types)
        return self.state.hero_types[DEFAULT_HERO_KEY]

    def _on_command(self, sp_command: SpCommand, player_index: int, team_only: Optional[bool]=None) -> CommandReturn:
        player = self.state.players[player_index]
        name, *args = sp_command.command_string.split(' ')
        self.fire_command(Command(name, player, args))
        return CommandReturn.BLOCK

    def _on_solo_event(self, game_event: GameEvent):
        event_args = game_event.variables.as_dict()
        player = self.state.players.from_userid(event_args.pop('userid'))
        self.fire_event(Event(game_event.name, player, event_args))

    def _on_duo_event(self, game_event: GameEvent):
        event_args = game_event.variables.as_dict()
        try:
            attacker = self.state.players.from_userid(event_args.pop('attacker'))
        except ValueError:
            attacker = None
        victim = self.state.players.from_userid(event_args.pop('userid'))
        event_args.update(attacker=attacker, victim=victim)
        victim_event, attacker_event, self_event = DUO_PLAYER_EVENTS[game_event.name]
        if attacker is None:
            self.fire_event(Event(self_event, victim, event_args))
        else:
            self.fire_event(Event(victim_event, victim, event_args))
            self.fire_event(Event(attacker_event, attacker, event_args))

    def fire_command(self, command: Command):
        for handler in self._command_handlers[command.name]:
            handler(command)

    def fire_event(self, event: Event):
        for handler in self._event_handlers[event.name]:
            handler(event)

    def load(self):
        for system in self.systems.values():
            system.load()
            for command, handler in system.command_handlers.items():
                self._command_handlers[command].append(handler)
            for event, handler in system.event_handlers.items():
                self._event_handlers[event].append(handler)

        for command in self._command_handlers.keys():
            client_command_manager.register_commands(f'hw_{command}', self._on_command)
            say_command_manager.register_commands(command, self._on_command)

        for event in DUO_PLAYER_EVENTS.keys():
            event_manager.register_for_event(event, self._on_duo_event)
        for event in SOLO_PLAYER_EVENTS:
            event_manager.register_for_event(event, self._on_solo_event)

    def unload(self):
        for event in DUO_PLAYER_EVENTS.keys():
            event_manager.unregister_for_event(event, self._on_duo_event)
        for event  in SOLO_PLAYER_EVENTS:
            event_manager.unregister_for_event(event, self._on_solo_event)

        for command in self._command_handlers.keys():
            client_command_manager.unregister_commands(f'hw_{command}', self._on_command)
            say_command_manager.unregister_commands(command, self._on_command)

        for system in self.systems.values():
            system.unload()


hw = HeroWars()
load = hw.load
unload = hw.unload


# Custom commands

@ClientCommand('+ultimate')
def _cmd_ultimate(command, player_index):
    player = hw.state.players[player_index]
    hw.fire_event(Event('player_ultimate', player, {}))


@ClientCommand('-ultimate')
def _cmd_ultimate(command, player_index):
    player = hw.state.players[player_index]
    hw.fire_event(Event('player_ultimate_end', player, {}))


@ClientCommand('+ability')
def _cmd_ability(command, player_index):
    player = hw.state.players[player_index]
    hw.fire_event(Event('player_ability', player, {}))


@ClientCommand('-ability')
def _cmd_ability(command, player_index):
    player = hw.state.players[player_index]
    hw.fire_event(Event('player_ability_end', player, {}))


@ClientCommand('hw_heroinfo')
@SayCommand('heroinfo')
def _cmd_heroinfo(command, player_index, team_only=None):
    player = hw.state.players[player_index]
    hero = player.hero
    player.chat(strings.hero_info,
        name=hero.name,
        level=hero.level,
        xp=hero.xp,
        required_xp=hero.required_xp,
    )
    return CommandReturn.BLOCK


@ClientCommand('hw_resetskills')
@SayCommand('resetskills')
def _cmd_resetskills(command, player_index, team_only=None):
    player = hw.state.players[player_index]
    player.hero.reset_skills()
    player.chat(strings.unspent_skill_points,
        hero_name=player.hero.name,
        skill_points=player.hero.skill_points
    )
    return CommandReturn.BLOCK


# Custom events

@OnPlayerChangeHero
def _on_hero_change(player, **event_args):
    hw.fire_event(Event('player_change_hero', player, event_args))
    if not player.dead:
        player.slay()
    player._init_hero()
    player.chat(strings.change_hero, hero_name=player.hero.name)


@OnHeroLevelUp
def _on_hero_level_up(player, **event_args):
    hw.fire_event(Event('hero_level_up', player, event_args))
    hero = player.hero
    player.chat(strings.hero_info,
        name=hero.name,
        level=hero.level,
        xp=hero.xp,
        required_xp=hero.required_xp,
    )


@EntityPreHook(EntityCondition.is_player, 'on_take_damage')
def _trigger_pre_damage_skills(args):
    take_damage_info = make_object(TakeDamageInfo, args[1])
    if not take_damage_info.attacker:
        return
    attacker = hw.state.players[take_damage_info.attacker]
    victim = hw.state.players[index_from_pointer(args[0])]
    if victim.team == attacker.team:
        return
    event_args = {
        'attacker': attacker,
        'victim': victim,
        'take_damage_info': take_damage_info,
    }
    attacker.hero.trigger_skills('pre_player_attack', {'player': attacker, **event_args})
    victim.hero.trigger_skills('pre_player_victim', {'player': victim, **event_args})


@SpEvent('player_spawn')
def on_spawn(event):
    player = hw.state.players.from_userid(event['userid'])
    hero = player.hero
    player.chat(strings.hero_info,
        name=hero.name,
        level=hero.level,
        xp=hero.xp,
        required_xp=hero.required_xp,
    )
    if player.hero.skill_points > 0:
        pass 

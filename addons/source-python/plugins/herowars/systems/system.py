# Python imports
from typing import Any, Callable, Dict, Tuple

# Site-Package imports
from dataclasses import dataclass

# Hero-Wars imports
from ..plugin_state import PluginState
from ..player import Player


CommandArgs = Tuple[str]
EventArgs = Dict[str, Any]


@dataclass
class Command:
    name: str
    player: Player
    args: CommandArgs


@dataclass
class Event:
    name: str
    player: Player
    args: EventArgs


CommandHandler = Callable[[Command], None]
EventHandler = Callable[[Event], None]


class System:

    def __init__(self, state: PluginState):
        self._state = state
        self._command_handlers = {}
        self._event_handlers = {}

    @property
    def state(self):
        return self._state

    @property
    def command_handlers(self):
        return self._command_handlers

    @property
    def event_handlers(self):
        return self._event_handlers

    def load(self):
        self._command_handlers = self._init_command_handlers()
        self._event_handlers = self._init_event_handlers()

    def unload(self):
        pass

    def _init_command_handlers(self) -> Dict[str, CommandHandler]:
        return {}

    def _init_event_handlers(self) -> Dict[str, EventHandler]:
        return {}

    def trigger_command(self, command: Command):
        callback = self.command_handlers.get(command.name)
        if callback is not None:
            callback(command)

    def trigger_event(self, event: Event):
        callback = self.event_handlers.get(event.name)
        if callback is not None:
            callback(event)

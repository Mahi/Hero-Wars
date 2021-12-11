# Python imports
from typing import Dict

# Source.Python imports
from messages.colors.saytext2 import GREEN, ORANGE, WHITE

# Hero-Wars imports
from .. import strings
from ..constants import XP_ON_KILL
from ..listeners import OnHeroLevelUp
from .system import Event, EventHandler, System


class XpSystem(System):

    def _init_event_handlers(self) -> Dict[str, EventHandler]:
        return {
            'player_kill': self._give_xp,
        }

    def _give_xp(self, event: Event):
        player = event.player
        old_level = player.hero.level
        player.hero.xp += XP_ON_KILL
        player.chat(strings.messages['Kill XP'], xp=XP_ON_KILL, color=GREEN, white=WHITE)
        if player.hero.level > old_level:
            OnHeroLevelUp.manager.notify(
                player=player,
                hero=player.hero,
                old_level=old_level,
                new_level=player.hero.level,
            )

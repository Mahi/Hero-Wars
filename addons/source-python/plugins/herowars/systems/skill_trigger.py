# Python imports
from typing import Dict

# Hero-Wars imports
from ..constants import ALL_EVENTS
from .system import Event, EventHandler, System


class SkillTriggerSystem(System):

    def _init_event_handlers(self) -> Dict[str, EventHandler]:
        return {
            event_name: self.trigger_skills
            for event_name in ALL_EVENTS
        }

    def trigger_skills(self, event: Event):
        event.player.hero.trigger_skills(event.name, {'player': event.player, **event.args})

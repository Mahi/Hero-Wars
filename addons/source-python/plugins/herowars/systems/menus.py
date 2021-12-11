# Python imports
from functools import partial
from typing import Any, Callable, Dict, Optional

# Source.Python imports
from menus import PagedMenu as Menu, PagedOption as Option, Text
from messages.colors.saytext2 import ORANGE

# Hero-Wars imports
from .. import strings
from ..entities import Hero, Skill
from ..listeners import OnPlayerChangeHero
from ..player import Player
from ..utils import create_translation_string, split_translation_string
from .system import Command, CommandHandler, Event, EventHandler, System


BuildCallback = Callable[[Menu, Player], None]
SelectCallback = Callable[[Menu, Player, Any], Optional[Menu]]


class _SkillMenu(Menu):

    def __init__(self, *args, skill: Optional[Skill]=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.skill = skill


class MenuSystem(System):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main = self._menu('Hero-Wars', self._main_build, self._main_select)
        self.change_hero = self._menu(
            strings.menus['Change Hero'],
            self._change_hero_build,
            self._change_hero_select,
            parent=self.main,
        )
        self.view_skills = self._menu(
            strings.menus['View Skills'],
            self._view_skills_build,
            parent=self.main,
        )
        self.upgrade_skills = self._menu(
            strings.menus['Upgrade Skills'],
            self._upgrade_skills_build,
            self._upgrade_skills_select,
            parent=self.main,
        )

    def _init_command_handlers(self) -> Dict[str, CommandHandler]:
        return {
            'hw': partial(self._send_menu, self.main),
            'herowars': partial(self._send_menu, self.main),
            'changehero': partial(self._send_menu, self.change_hero),
            'viewskills': partial(self._send_menu, self.view_skills),
            'upgradeskills': partial(self._send_menu, self.upgrade_skills),
        }

    def _init_event_handlers(self) -> Dict[str, EventHandler]:
        return {
            'player_spawn': self._send_upgrade_skills,
            'player_change_hero': partial(self._send_menu, self.view_skills),
        }

    def _menu(self,
        title: Optional[str]=None, 
        build_callback: Optional[BuildCallback]=None,
        select_callback: Optional[SelectCallback]=None,
        parent: Optional[Menu]=None,
    ) -> Menu:
        return Menu(
            title=title,
            build_callback=self._build(build_callback),
            select_callback=self._select(select_callback),
            parent_menu=parent,
        )

    def _send_menu(self, menu: Menu, command: Command):
        menu.send(command.player.index)

    def _send_upgrade_skills(self, event: Event):
        if event.player.hero.skill_points <= 0:
            return
        for skill in event.player.hero.skills:
            if not skill.level >= skill.max_level:
                self.upgrade_skills.send(event.player.index)
                return

    def _build(self, callback: BuildCallback) -> Callable[[Menu, int], None]:
        def build_callback(menu, player_index):
            menu.clear()
            return callback(menu, self.state.players[player_index])
        return build_callback

    def _select(self, callback: SelectCallback) -> Callable[[Menu, int, Any], Optional[Menu]]:
        def select_callback(menu, player_index, choice):
            return callback(menu, self.state.players[player_index], choice)
        return select_callback

    def _main_build(self, menu: Menu, player: Player):
        menu.description = player.hero.name
        menu.extend([
            Option(strings.menus['Change Hero'], self.change_hero),
            Option(strings.menus['View Skills'], self.view_skills),
            Option(strings.menus['Upgrade Skills'], self.upgrade_skills),
            Option(strings.menus['Reset Skills'], 'RESET'),
        ])

    def _main_select(self, menu: Menu, player: Player, choice: Any) -> Menu:
        if choice.value == 'RESET':
            player.hero.reset_skills()
            player.info(create_translation_string(
                f'{{unspent_message}}: {ORANGE}{player.hero.skill_points}',
                unspent_message=strings.messages['Unspent Skill Points'],
            ))
            return menu
        else:
            return choice.value

    def _change_hero_build(self, menu: Menu, player: Player):
        total_level = player.total_level()
        menu.description = create_translation_string(
            '{hero_name} ({total_level_str}: {total_level})',
            hero_name=player.hero.name,
            total_level_str=strings.common['Total Level'],
            total_level=total_level,
        )
        for hero_type in self.state.hero_types.values():
            available = hero_type.required_level <= total_level
            if not available:
                text = create_translation_string(
                    '{hero_name} ({required_str}: {required_level})',
                    hero_name=hero_type.name,
                    required_str=strings.common['Required'],
                    required_level=hero_type.required_level,
                )
            else:
                hero = player.heroes.get(hero_type.key, None)
                level = hero.level if hero is not None else 0
                text = create_translation_string(
                    '{hero_name} ({level_str}: {level})',
                    hero_name=hero_type.name,
                    level_str=strings.common['Level'],
                    level=level,
                )
            menu.append(Option(text, hero_type.key, highlight=available, selectable=available))

    def _change_hero_select(self, menu: Menu, player: Player, choice: Any):
        if choice.value is None:
            return
        old_hero = player.hero
        if choice.value not in player.heroes:
            player.heroes[choice.value] = Hero(self.state.hero_types[choice.value])
        player.hero = player.heroes[choice.value]
        OnPlayerChangeHero.manager.notify(
            player=player,
            old_hero=old_hero,
            new_hero=player.hero,
        )

    def _view_skills_build(self, menu: Menu, player: Player):
        menu.description = player.hero.name
        page = 0
        option_count = 0
        skill_index = 0
        for skill in player.hero.skills:
            description = [
                Text(create_translation_string('  {row}', row=row))
                for row in split_translation_string(skill.description)
            ]
            if option_count + 1 + len(description) > menu._get_max_item_count():
                menu.extend([Text(' ') for _ in range(menu._get_max_item_count() - option_count)])
                page += 1
                option_count = 0
            option_count += 1  # Skill name
            option_count += len(description)
            if skill.passive:
                prefix = ''
                passive_text = create_translation_string(' ({passive})', passive=strings.common['Passive'])
            else:
                skill_index += 1
                prefix = f'{skill_index}. '
                passive_text = ''
            if 'player_ultimate' in skill.type_object.event_callbacks:
                ultimate_text = create_translation_string(' ({ultimate})', ultimate=strings.common['Ultimate'])
            else:
                ultimate_text = ''
            menu.append(Text(create_translation_string(
                '->{prefix}{skill}{ultimate}{passive}',
                prefix=prefix,
                skill=skill.name,
                ultimate=ultimate_text,
                passive=passive_text,
            )))
            menu.extend(description)

    def _upgrade_skills_build(self, menu: Menu, player: Player):
        menu.description = create_translation_string(
            '{hero_name} ({skill_points_str}: {skill_points})',
            hero_name=player.hero.name,
            skill_points_str=strings.common['Skill Points'],
            skill_points=player.hero.skill_points,
        )
        for skill in player.hero.skills:
            if skill.passive:
                continue
            can_upgrade = player.hero.can_upgrade_skill(skill)
            text = create_translation_string(
                '{skill_name} ({skill_level}/{skill_max_level})',
                skill_name=skill.name,
                skill_level=skill.level,
                skill_max_level=skill.max_level,
            )
            menu.append(Option(text, skill.key, highlight=can_upgrade, selectable=can_upgrade))

    def _upgrade_skills_select(self, menu: Menu, player: Player, choice: Any):
        for skill in player.hero.skills:
            if skill.key == choice.value:
                if player.hero.can_upgrade_skill(skill):
                    skill.level += 1
                    player.info(create_translation_string(
                        '{skill_name} {upgraded_str}',
                        skill_name=skill.name,
                        upgraded_str=strings.common['Upgraded'],
                    ))
                break
        return menu

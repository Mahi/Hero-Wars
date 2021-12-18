# Python imports
from typing import Any, Callable, Optional

# Source.Python imports
from menus import PagedMenu as Menu, PagedOption as Option, Text
from messages.colors.saytext2 import ORANGE

# Hero-Wars imports
from . import strings
from .entities import Hero
from .events import events
from .hero_types import hero_types
from .player import Player
from .players import player_dict
from .utils import create_translation_string, split_translation_string


BuildCallback = Callable[[Menu, Player], None]
SelectCallback = Callable[[Menu, Player, Any], Optional[Menu]]


def _menu(
    title: Optional[str]=None, 
    build_callback: Optional[BuildCallback]=None,
    select_callback: Optional[SelectCallback]=None,
) -> Menu:
    return Menu(
        title=title,
        build_callback=_build(build_callback),
        select_callback=_select(select_callback),
    )


def _build(callback: BuildCallback) -> Callable[[Menu, int], None]:
    def build_callback(menu, player_index):
        menu.clear()
        return callback(menu, player_dict[player_index])
    return build_callback


def _select(callback: SelectCallback) -> Callable[[Menu, int, Any], Optional[Menu]]:
    def select_callback(menu, player_index, choice):
        return callback(menu, player_dict[player_index], choice)
    return select_callback


def _main_build(menu: Menu, player: Player):
    menu.description = player.hero.name
    menu.extend([
        Option(strings.menus['Change Hero'], change_hero),
        Option(strings.menus['Upgrade Skills'], upgrade_skills),
        Option(strings.menus['View Heroes'], view_heroes),
        Option(strings.menus['View Skills'], view_skills),
        Option(strings.menus['Reset Skills'], 'RESET'),
    ])


def _main_select(menu: Menu, player: Player, choice: Any) -> Menu:
    if choice.value == 'RESET':
        player.hero.reset_skills()
        player.info(create_translation_string(
            f'{{unspent_message}}: {ORANGE}{player.hero.skill_points}',
            unspent_message=strings.messages['Unspent Skill Points'],
        ))
        return menu
    choice.value.parent = menu
    return choice.value


def _change_hero_build(menu: Menu, player: Player):
    total_level = player.total_level()
    menu.description = create_translation_string(
        '{hero_name} ({total_level_str}: {total_level})',
        hero_name=player.hero.name,
        total_level_str=strings.common['Total Level'],
        total_level=total_level,
    )
    for hero_type in hero_types.values():
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


def _change_hero_select(menu: Menu, player: Player, choice: Any):
    if choice.value is None:
        return
    old_hero = player.hero
    if choice.value not in player.heroes:
        player.heroes[choice.value] = Hero(hero_types[choice.value])
    player.hero = player.heroes[choice.value]
    events['player_change_hero'].fire(
        player=player,
        old_hero=old_hero,
        new_hero=player.hero,
    )


def _view_heroes_build(menu: Menu, player: Player):
    for hero_type in hero_types.values():
        menu.append(Option(hero_type.name, value=hero_type.key))
    return menu


def _view_heroes_select(menu: Menu, player: Player, choice: Any):
    view_skills.parent = menu
    view_skills.hero = hero_types[choice.value]
    return view_skills


def _view_skills_build(menu: Menu, player: Player):
    if menu.hero is None:
        menu.hero = player.hero
    menu.description = menu.hero.name
    page = 0
    option_count = 0
    skill_index = 0
    for skill in menu.hero.skills:
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
        if 'player_ultimate' in skill.event_callbacks:
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


def _upgrade_skills_build(menu: Menu, player: Player):
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


def _upgrade_skills_select(menu: Menu, player: Player, choice: Any):
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


main = _menu('Hero-Wars', _main_build, _main_select)
change_hero = _menu(strings.menus['Change Hero'], _change_hero_build, _change_hero_select)
view_heroes = _menu(strings.menus['View Heroes'], _view_heroes_build, _view_heroes_select)
view_skills = _menu(strings.menus['View Skills'], _view_skills_build)
view_skills.hero = None
upgrade_skills = _menu(strings.menus['Upgrade Skills'], _upgrade_skills_build, _upgrade_skills_select)

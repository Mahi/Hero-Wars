# Site-Package imports
from dataclasses import dataclass
from sqlalchemy import create_engine, Column, ForeignKey, Integer, MetaData, Table, Text
from sqlalchemy.engine.url import URL
from sqlalchemy.sql import select
from sqlalchemy.sql.expression import bindparam

# Hero-Wars imports
from . import config
from .entities import Hero
from .hero_types import hero_types
from .player import Player


_metadata = MetaData()


@dataclass
class _Tables:
    player: Table
    hero: Table
    skill: Table


_t = _Tables(
    player=Table('player', _metadata,
        Column('steamid', Text, primary_key=True),
        Column('hero_id', Integer, ForeignKey('hero.id')),
    ),
    hero=Table('hero', _metadata,
        Column('id', Integer, primary_key=True),
        Column('key', Text, nullable=False),
        Column('level', Integer),
        Column('xp', Integer),
        Column('steamid', Integer, ForeignKey('player.steamid'), nullable=False),
    ),
    skill=Table('skill', _metadata,
        Column('id', Integer, primary_key=True),
        Column('key', Text, nullable=False),
        Column('level', Integer),
        Column('hero_id', Integer, ForeignKey('hero.id'), nullable=False),
    ),
)


url_dict = {}
for key, cvar in config.db_url.items():
    value = cvar.get_string()
    if not value:
        value = None
    url_dict[key] = value

engine = create_engine(URL(**url_dict))
_metadata.create_all(bind=engine)


def create_player_data(player: Player):
    with engine.connect() as conn:
        conn.execute(
            _t.player.insert().values(steamid=player.steamid)
        )

        create_hero_data(player.hero, steamid=player.steamid)

        conn.execute(
            _t.player.update()\
                .where(_t.player.c.steamid==player.steamid)\
                .values(hero_id=player.hero._db_id)
        )


def load_player_data(player: Player) -> bool:
    with engine.connect() as conn:
        player_result = conn.execute(
            select([_t.player]).where(_t.player.c.steamid==player.steamid)
        )
        player_info = player_result.first()
        if player_info is None:
            return False

        heroes_result = conn.execute(
            select([_t.hero]).where(_t.player.c.steamid==player.steamid)
        )
        for hero_info in heroes_result:
            hero_type = hero_types.get(hero_info.key)
            if hero_type is None:
                continue
            hero = Hero(hero_type, level=hero_info.level, xp=hero_info.xp, db_id=hero_info.id)
            player.heroes[hero_type.key] = hero

            if hero_info.id == player_info.hero_id:
                player.hero = hero

        return True


def load_skills_data(hero: Hero):
    with engine.connect() as conn:
        skills = {skill.key: skill for skill in hero.skills if not skill.passive}
        skills_result = conn.execute(
            select([_t.skill]).where(_t.hero.c.id==hero._db_id)
        )
        for skill_info in skills_result:
            skill = skills.get(skill_info.key)
            if skill:
                skill.level = skill_info.level
                skill._db_id = skill_info.id


def save_player_data(player: Player):
    with engine.connect() as conn:
        conn.execute(
            _t.player.update()\
                .where(_t.player.c.steamid==player.steamid)\
                .values(hero_id=player.hero._db_id)
        )
        save_hero_data(player.hero)


def create_hero_data(hero: Hero, steamid: str):
    with engine.connect() as conn:
        result = conn.execute(
            _t.hero.insert().values(
                key=hero.key,
                level=hero.level,
                xp=hero.xp,
                steamid=steamid,
            )
        )
        hero._db_id = result.inserted_primary_key[0]

        skills = [skill for skill in hero.skills if not skill.passive]
        skills_result = conn.execute(
            _t.skill.insert().values([
                {
                    'key': skill.key,
                    'level': skill.level,
                    'hero_id': hero._db_id,
                }
                for skill in skills
            ])
        )
        last_id = skills_result.inserted_primary_key[0]
        first_id = last_id - len(skills) + 1
        ids = range(first_id, last_id + 1)
        for skill, skill_id in zip(skills, ids):
            skill._db_id = skill_id


def save_hero_data(hero: Hero):
    with engine.connect() as conn:
        conn.execute(
            _t.hero.update()\
                .where(_t.hero.c.id==hero._db_id)\
                .values(key=hero.key, level=hero.level, xp=hero.xp)
        )
        conn.execute(
            _t.skill.update()\
                .where(_t.skill.c.id==bindparam('id_'))\
                .values(level=bindparam('level')),
            [
                {
                    'level': skill.level,
                    'id_': skill._db_id,
                }
                for skill in hero.skills if not skill.passive
            ]
        )

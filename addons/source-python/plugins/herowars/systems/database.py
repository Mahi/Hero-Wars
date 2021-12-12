# Python imports
from typing import Dict, Optional, Tuple

# Site-Package imports
from sqlalchemy import create_engine, Column, ForeignKey, Integer, MetaData, Table, Text
from sqlalchemy.engine.url import URL
from sqlalchemy.sql import select
from sqlalchemy.sql.expression import bindparam

# Hero-Wars imports
from ..constants import DATABASE_URL
from ..entities import Hero
from ..player import Player
from .system import Event, EventHandler, System


def _schema(metadata: MetaData) -> Tuple[Table]:
    return (
        Table('player', metadata,
            Column('steamid', Text, primary_key=True),
            Column('hero_id', Integer, ForeignKey('hero.id')),
        ),
        Table('hero', metadata,
            Column('id', Integer, primary_key=True),
            Column('key', Text, nullable=False),
            Column('level', Integer),
            Column('xp', Integer),
            Column('steamid', Integer, ForeignKey('player.steamid'), nullable=False),
        ),
        Table('skill', metadata,
            Column('id', Integer, primary_key=True),
            Column('key', Text, nullable=False),
            Column('level', Integer),
            Column('hero_id', Integer, ForeignKey('hero.id'), nullable=False),
        ),
    )


class DatabaseSystem(System):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._metadata = MetaData()
        self.players, self.heroes, self.skills = _schema(self._metadata)
        self._engine = create_engine(URL(**DATABASE_URL))
        self._metadata.create_all(bind=self._engine)

    def unload(self):
        super().unload()
        for player in self.state.players.values():
            self.save_player_data(player)

    def _init_event_handlers(self) -> Dict[str, EventHandler]:
        return {
            'player_disconnect': self._save_player_on_event,
            'player_death': self._save_player_on_event,
            'player_suicide': self._save_player_on_event,
            'player_change_hero': self._on_player_change_hero,
        }

    def _save_player_on_event(self, event: Event):
        if event.player.is_bot():
            return
        self.save_player_data(event.player)

    def _on_player_change_hero(self, event: Event):
        if event.player.is_bot():
            return
        if event.args['new_hero']._db_id is None:
            self.create_hero_data(event.args['new_hero'], steamid=event.player.steamid)
        self.save_hero_data(event.args['old_hero'])

    def create_player_data(self, player: Player):
        with self._engine.connect() as conn:
            conn.execute(
                self.players.insert().values(steamid=player.steamid)
            )

            self.create_hero_data(player.hero, steamid=player.steamid)

            conn.execute(
                self.players.update().where(self.players.c.steamid==player.steamid).values(hero_id=player.hero._db_id)
            )

    def load_player_data(self, player: Player) -> bool:
        with self._engine.connect() as conn:
            player_result = conn.execute(
                select([self.players]).where(self.players.c.steamid==player.steamid)
            )
            player_info = player_result.first()
            if player_info is None:
                return False

            heroes_result = conn.execute(
                select([self.heroes]).where(self.players.c.steamid==player.steamid)
            )
            for hero_info in heroes_result:
                hero_type = self.state.hero_types.get(hero_info.key)
                if hero_type is None:
                    continue
                hero = Hero(hero_type, level=hero_info.level, xp=hero_info.xp, db_id=hero_info.id)
                player.heroes[hero_type.key] = hero

                if hero_info.id != player_info.hero_id:
                    continue

                player.hero = hero
                skills = {skill.key: skill for skill in player.hero.skills if not skill.passive}
                skills_result = conn.execute(
                    select([self.skills]).where(self.heroes.c.id==hero_info.id)
                )
                for skill_info in skills_result:
                    skill = skills.get(skill_info.key)
                    if skill:
                        skill.level = skill_info.level
                        skill._db_id = skill_info.id
            return True

    def save_player_data(self, player: Player):
        with self._engine.connect() as conn:
            conn.execute(
                self.players.update().where(self.players.c.steamid==player.steamid).values(hero_id=player.hero._db_id)
            )
            self.save_hero_data(player.hero)

    def create_hero_data(self, hero: Hero, steamid: str):
        with self._engine.connect() as conn:
            result = conn.execute(
                self.heroes.insert().values({
                    'key': hero.key,
                    'level': hero.level,
                    'xp': hero.xp,
                    'steamid': steamid,
                })
            )
            hero._db_id = result.inserted_primary_key[0]

            skills = [skill for skill in hero.skills if not skill.passive]
            skills_result = conn.execute(
                self.skills.insert().values([
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

    def save_hero_data(self, hero: Hero):
        with self._engine.connect() as conn:
            conn.execute(
                self.heroes.update().where(self.heroes.c.id==hero._db_id).values(
                    key=hero.key,
                    level=hero.level,
                    xp=hero.xp,
                )
            )
            conn.execute(
                self.skills.update().where(self.skills.c.id==bindparam('id_')).values(level=bindparam('level')),
                [
                    {
                        'level': skill.level,
                        'id_': skill._db_id,
                    }
                    for skill in hero.skills if not skill.passive
                ]
            )

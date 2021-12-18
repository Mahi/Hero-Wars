# Hero-Wars 

Hero-Wars is a server-sided [Source.Python](https://sourcepython.com/) plugin for CS:GO.

Hero-Wars extends the standard gameplay with _heroes_ — unique characters that
give your CS:GO player all sorts of magical powers.
These powers are referred to as _skills_, each of which has its unique effect on the player.

It's basically similar to Overwatch or Valorant, but better because it's CS:GO.
So yet another implementation of the Warcraft-mod.

## How to install?

You will need to install all the dependencies to your game server first:

1. [Source.Python](https://sourcepython.com/) allows you to run Python mods on the server.
2. [EasyPlayer](https://github.com/Mahi/EasyPlayer) implements additional features for players.
3. [PyYAML](https://pypi.org/project/PyYAML) is used to read the hero files.
    You can install PyYaml with:
    `py -3 -m pip install PyYAML -t [YOUR_CSGO_DIR]/csgo/addons/source-python/packages/site-packages`,
    obviously replacing `[YOUR_CSGO_DIR]` with your CS:GO directory.
4. [Dataclasses](https://pypi.org/project/dataclasses/) are a Python 3.7 feature that is not available
    on Source.Python yet. Installation is equivalent to PyYAML:
   `py -3 -m pip install dataclasses -t [YOUR_CSGO_DIR]/csgo/addons/source-python/packages/site-packages`.

_(Hopefully dependencies 3 and 4 will be included with Source.Python eventually)_

Finally download and extract Hero-Wars to your CSGO directory.
There are no GitHub releases yet, so you'll have to clone or download the repository.

## How to run?

Once you've installed all the dependencies and have Source.Python running on you server,
you may load Hero-Wars with:

    sp plugin load herowars

This should create a `csgo/cfg/herowars` directory with the following files in it:

- `main.cfg` for generic Hero-Wars settings.
- `database.cfg` for database specific settings — update this with your database information!
- `xp.cfg` for XP gain settings.

You may freely edit these, and feel free to ask for help on
[Source.Python forums](https://sourcepython.com) or via GitHub issues.

## How to play?

Type `!hw` to the CS:GO chat while you're on the server,
and you'll get a menu with all the functionality available.
From here you can choose a hero, upgrade its skills, and more.

## How to make heroes?

Each hero consists of three files:

- `data.yml` for all the numeric data for the hero. Damage values, durations, chances, etc.
    This allows server owners to easily balance the heroes without having to touch any code.
    It's how all modern games are implemented, get used to it.
- `code.py` for the functionality of the hero.
    Each skill is its own Python `class` with event names as methods.
    There's also a special `init(player, hero, skill)` method for initializing skill variables.
- `strings.yml` for all the strings for the hero. Name, description, skill messages, etc.

I might make a fully fledged guide one day, but for now you have to copy existing heroes
in the `csgo/addons/source-python/plugins/herowars/heroes` directory.

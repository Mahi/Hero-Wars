# Source.Python imports
from commands import CommandReturn
from commands.client import ClientCommand
from entities import TakeDamageInfo
from entities.helpers import index_from_pointer
from entities.hooks import EntityCondition
from entities.hooks import EntityPreHook
from memory import make_object

# Custom package imports
from easyevents import EventManager

# Hero-Wars imports
from .constants import CUSTOM_PLAYER_EVENTS
from .players import player_dict


events = EventManager(player_dict)

for event_name in CUSTOM_PLAYER_EVENTS:
    events.create_event(event_name)


@EntityPreHook(EntityCondition.is_player, 'on_take_damage')
def _fire_pre_take_damage(args):
    take_damage_info = make_object(TakeDamageInfo, args[1])
    victim_index = index_from_pointer(args[0])
    victim = player_dict[victim_index]
    if take_damage_info.attacker and take_damage_info.attacker != victim_index:
        attacker = player_dict[take_damage_info.attacker]
    else:
        attacker = None
    event_args = {
        'attacker': attacker,
        'victim': victim,
        'take_damage_info': take_damage_info,
    }
    if attacker is not None:
        events['pre_player_attack'].fire(event_args, player=attacker)
    events['pre_player_victim'].fire(event_args, player=victim)


@ClientCommand('+ultimate')
def _fire_ultimate(command, player_index):
    player = player_dict[player_index]
    events['player_ultimate'].fire(player=player)
    return CommandReturn.BLOCK


@ClientCommand('-ultimate')
def _fire_ultimate_end(command, player_index):
    player = player_dict[player_index]
    events['player_ultimate_end'].fire(player=player)
    return CommandReturn.BLOCK


@ClientCommand('+ability')
def _fire_ability(command, player_index):
    player = player_dict[player_index]
    events['player_ability'].fire(player=player)
    return CommandReturn.BLOCK


@ClientCommand('-ability')
def _fire_ability_end(command, player_index):
    player = player_dict[player_index]
    events['player_ability_end'].fire(player=player)
    return CommandReturn.BLOCK

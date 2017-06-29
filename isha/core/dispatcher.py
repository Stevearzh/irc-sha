from isha.dict.event import EVENT
from .parser import card_parser

class dispatcher:
    def __init__(self, table):
        self.__table = table

    def __call__(self, event_why, obj, from_whom, to_whom=None):
        from_nick = self.__table.choose_player_by_nick(from_whom)
        to_nick   = self.__table.choose_player_by_nick(to_whom) if to_whom else None
        if event_why == EVENT['card_used']:
            card_parser(self.__table, obj, from_nick, to_nick)

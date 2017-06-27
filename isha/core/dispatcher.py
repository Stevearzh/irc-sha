from isha.dict.event import EVENT
from .parser import card_parser

class dispatcher:
    def __init__(self, table):
        self.__table = table

    def __call__(self, event_why, obj, from_whom, to_whom=None):
        if event_why == EVENT['card_used']:
            return card_parser(self.__table, obj, from_whom, to_whom)

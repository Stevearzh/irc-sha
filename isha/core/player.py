from transitions import Machine

from isha.dict.identity import IDENTITY
from isha.dict.status import STATUS_DICT, STATUS, TRANSITIONS

class player:
    def __init__(self, nick):
        self.__nick    = nick   # player's nick in irc
        self.__alive   = True
        self.__max_hp  = 0
        self.__hp      = 0
        self.__range   = 1
        self.__use_sha = True
        self.__cards   = []
        self.__id      = IDENTITY['unknown']
        self.__machine = Machine(model=self, states=STATUS, initial=STATUS_DICT['normal'])

        list(map(lambda t: self.__machine.add_transition(t['trigger'], t['source'], t['dest']), TRANSITIONS))

    def nick(self):
        return self.__nick

    def set_id(self, id):
        self.__id = id

    def secret(self):
        return self.__id

    def id(self):
        if self.is_king() or not(self.is_alive()):
            return self.__id
        else:
            return IDENTITY['unknown']

    def is_king(self):
        return self.__id == IDENTITY['king']

    def is_alive(self):
        return self.__alive

    def set_dead(self):
        self.__alive = False

    def max_hp(self):
        return self.__max_hp

    def change_max_hp(self, value):
        self.__max_hp = value

    def hp(self):
        return self.__hp

    def set_initial_hp(self, value):
        self.change_max_hp(value)
        self.__hp = value

    def increase_hp(self):
        if self.__hp < self.__max_hp:
            self.__hp += 1
            return True
        else:
            return False

    def decrease_hp(self, value):
        self.__hp -= value

    def range(self):
        return self.__range

    def get_card(self, card):
        self.__cards.append(card)

    def card(self):
        return self.__cards

    def choose_card(self, card):
        if card:
            index = self.__cards.index(card)
            return self.__cards.pop(index)

    def can_use_sha(self):
        return self.__use_sha

    def used_sha(self):
        self.__use_sha = False

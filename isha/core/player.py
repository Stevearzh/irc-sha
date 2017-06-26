from isha.dict.identity import IDENTITY
from isha.dict.card import CARD_SUIT

class player:
    def __init__(self, nick):
        self.__nick   = nick   # player's nick in irc
        self.__alive  = True
        self.__max_hp = 0
        self.__hp     = 0
        self.__seat   = -1
        self.__cards  = []
        self.__id     = None

    def nick(self):
        return self.__nick

    def set_id(self, id):
        self.__id = id

    def secret(self):
        return self.__id

    def id(self):
        if self.is_king() or self.is_dead():
            return self.__id
        else:
            return IDENTITY['unknown']

    def is_king(self):
        return self.__id == IDENTITY['king']

    def is_alive(self):
        return self.__alive

    def set_alive(self):
        self.__alive = True

    def is_dead(self):
        return not(self.__alive)

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

    def set_seat(self, seat):
        self.__seat = seat

    def seat(self):
        return self.__seat

    def get_card(self, card):
        self.__cards.append(card)

    def card(self):
        return self.__cards

    def explain_card_choose(self):
        return '，'.join([
            '使用 <花色><点数><名字> 来选取你要出的牌',
            '使用 S 来表示花色黑桃 ♠',
            '使用 H 来表示花色红桃 ♥',
            '使用 C 来表示花色梅花 ♣',
            '使用 D 来表示花色方片 ♦',
            '例如：DK杀、d6闪、S9杀、h10杀、dq桃'
        ])

    def choose_card(self, string, stack):
        suit = {
            'S': CARD_SUIT['spade'],
            'H': CARD_SUIT['heart'],
            'C': CARD_SUIT['club'],
            'D': CARD_SUIT['diamond']
        }[string[0].upper()]

        if string[1] == '1':
            point = string[1: 3]
            name  = string[3:]
        else:
            point = string[1].upper()
            name  = string[2:]

        result = list(filter(lambda card: card.suit() == suit and card.point() == point and card.name() == name, stack))
        if len(result):
            return result[0]
        else:
            return None

    def use_card(self, card, stack):
        index = stack.index(card)
        stack.pop(index)

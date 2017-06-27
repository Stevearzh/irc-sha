import random
from functools import reduce, wraps

from .player import player
from .identity import gen_id_list
from .factory import card_generator
from .dispatcher import dispatcher
from .calculator import calculator

SUPPORTED_SIZE = [5, 8]

def process_pack(table):
    @wraps(table)
    def wrapper(self, card_path, nick_list, card_list=[]):
        '''Add default package if not added yet'''
        pro_card_list = list(card_list)

        try:
            pro_card_list.index('common')   # default card package
        except Exception as e:
            pro_card_list.insert(0, 'common')

        return table(self, card_path, nick_list, pro_card_list)
    return wrapper

class table:
    @process_pack
    def __init__(self, card_path, nick_list, card_list):
        self.__size = len(nick_list)        

        if not reduce(lambda res, num: res or self.__size == num, SUPPORTED_SIZE, False):
            raise ValueError('irc-sha now only support for 5 or 8 players!')
        else:
            self.__list = list(map(lambda p: player(p), nick_list))
            random.shuffle(self.__list)   # random players' position
            self.__set_ids(self.__size, self.__list, gen_id_list(self.__size))
            self.__list = self.__sort_by_id(self.__list, self.king_player())   # reseat player according to their id

        self.__card_stack = card_generator(card_path, card_list)
        self.__used_cards = []
        self.__card_type  = card_list
        self.__judgement  = dispatcher(self)
        self.__calculator = calculator(self)

    def __set_ids(self, length, nick_list, id_list):
        if not len(nick_list) == len(id_list):
            raise ValueError('two lists lengths not equal')

        list(map(lambda i: nick_list[i].set_id(id_list[i]), list(range(length))))

    def __sort_by_id(self, player_list, king):
        [result, i, j] = [[], player_list.index(king), 0]

        while i < len(player_list):
            result.append(player_list[i])
            i += 1
        while len(result) < len(player_list):
            result.append(player_list[j])
            j += 1

        return result

    def distance(self, nick_a=None, nick_b=None):
        return self.__calculator.distance(nick_a, nick_b)

    def damage(self, source_who, target_who):
        return self.__calculator.damage(source_who, target_who)

    def __show_player(self, player):
        nick   = player.nick()
        hp     = player.hp()
        max_hp = player.max_hp()
        id     = player.id()
        alive  = 'Yes' if player.is_alive() else 'No'

        return 'Nick: {0}, HP: {1}, Max HP: {2}, ID: {3}, Alive: {4}'.format(nick, hp, max_hp, id, alive)

    def show(self):
        result = 'Rest cards: {0}, Used cards: {1}\n\n'.format(self.rest_cards(), self.used_cards());
        result += '\n'.join(list(map(lambda player: self.__show_player(player), self.players())))
        return result

    def players(self):
        return self.__list

    def card_type(self):
        return self.__card_type

    def card_stack(self):
        return self.__card_stack

    def shuffle_card(self):
        random.shuffle(self.__card_stack)

    def deal_card(self):
        card = self.__card_stack.pop(0)
        if self.rest_cards() == 0:
            self.__transfer_to_stack()
        return card

    def drop_card(self, card):
        self.__used_cards.insert(len(self.__used_cards), card)

    def rest_cards(self):
        return len(self.__card_stack)

    def used_cards(self):
        return len(self.__used_cards)

    def insert_card_top(self, card):
        self.__card_stack.insert(0, card)

    def insert_card_bottom(self, card):
        self.__card_stack.insert(len(self.__card_stack), card)

    def __transfer_to_stack(self):
        list(map(lambda card: self.insert_card_top(card), self.__used_cards))
        self.__used_cards = []   # clear used cards stack
        self.shuffle_card()

    def king_player(self):
        return list(filter(lambda player: player.is_king(), self.__list))[0]

    def choose_player_by_nick(self, nick):
        return list(filter(lambda player: player.nick() == nick, self.__list))[0]

    def judge(self, *args, **kwargs):
        self.__judgement(*args, **kwargs)

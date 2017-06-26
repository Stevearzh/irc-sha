import random
from functools import reduce, wraps

from .player import player
from .identity import gen_id_list
from .factory import card_generator

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
        self.__size       = len(nick_list)
        self.__card_stack = card_generator(card_path, card_list)
        self.__card_type  = card_list

        if not reduce(lambda res, num: res or self.__size == num, SUPPORTED_SIZE, False):
            raise ValueError('irc-sha now only support for 5 or 8 players!')
        else:
            self.__list = list(map(lambda p: player(p), nick_list))
            random.shuffle(self.__list)   # random players' position
            self.__set_ids(self.__size, self.__list, gen_id_list(self.__size))
            self.__list = self.__sort_by_id(self.__list, self.king_player())   # reseat player according to their id
            self.__nicks = list(map(lambda p: p.nick(), self.__list))

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
        try:
            pos_a = self.__nicks.index(nick_a)
            pos_b = self.__nicks.index(nick_b)
            [max, min] = [pos_a, pos_b] if pos_a > pos_b else [pos_b, pos_a]

            distance = max - min
            if distance > self.__size / 2:
                distance = self.__size - distance
            return distance

        except Exception as e:
            return -1

    def __show_player(self, player):
        nick   = player.nick()
        hp     = player.hp()
        max_hp = player.max_hp()
        id     = player.id()

        return 'Nick: %s, HP: %d, Max HP: %d, ID: %s' % (nick, hp, max_hp, id)

    def show(self):
        return '\n'.join(list(map(lambda player: self.__show_player(player), self.players())))

    def players(self):
        return self.__list

    def card_type(self):
        return self.__card_type

    def card_stack(self):
        return self.__card_stack

    def shuffle_card(self):
        random.shuffle(self.__card_stack)

    def deal_card(self):
        return self.__card_stack.pop()

    def king_player(self):
        return list(filter(lambda player: player.is_king(), self.__list))[0]

    def choose_player_by_nick(self, nick):
        return list(filter(lambda player: player.nick() == nick, self.__list))[0]

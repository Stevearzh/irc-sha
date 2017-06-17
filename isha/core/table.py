import random
from functools import reduce, wraps

from .identity import gen_id_list
from .factory import card_generator
from isha.dict.identity import IDENTITY

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
            self.__list = list(nick_list)
            random.shuffle(self.__list)   # random players' position
            self.__secret = self.__merge_list(self.__size, self.__list, gen_id_list(self.__size))
            self.__detail = self.__set_cloak(self.__secret)   # cloak all identities except the king

    def __merge_list(self, length, nick_list, id_list):
        if not len(nick_list) == len(id_list):
            raise ValueError('two lists lengths not equal')

        return list(map(lambda i: ({
            'nick': nick_list[i],
            'id': id_list[i]
        }), list(range(length))))

    def __filter_id(self, id, ex):
        if id == ex:
            return id
        else:
            return '***'

    def __set_cloak(self, secret_list):
        return list(map(lambda p: ({
            'nick': p['nick'],
            'id': self.__filter_id(p['id'], IDENTITY['king'])
        }), secret_list))

    def distance(self, nick_a=None, nick_b=None):
        try:
            pos_a = self.__list.index(nick_a)
            pos_b = self.__list.index(nick_b)
            [max, min] = [pos_a, pos_b] if pos_a > pos_b else [pos_b, pos_a]

            distance = max - min
            if distance > self.__size / 2:
                distance = self.__size - distance
            return distance

        except Exception as e:
            return -1

    def secret(self):
        return self.__secret

    def show(self):
        return self.__detail

    def card_type(self):
        return self.__card_type

    def card_stack(self):
        return self.__card_stack

    def shuffle_card(self):
        random.shuffle(self.__card_stack)

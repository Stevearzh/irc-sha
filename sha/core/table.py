import random
from functools import reduce

from .identity import gen_id_list
from sha.dict.identity import IDENTITY

SUPPORTED_SIZE = [5, 8]

class table:
    def __init__(self, nick_list):
        self.__size = len(nick_list)

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

    def get_distance(self, nick_a=None, nick_b=None):
        try:
            pos_a = self.__position.index(nick_a)
            pos_b = self.__position.index(nick_b)
            [max, min] = [pos_a, pos_b] if pos_a > pos_b else [pos_b, pos_a]

            distance = max - min
            if distance > self.__size / 2:
                distance = self.__size - distance
            return distance

        except Exception as e:
            return -1

    def get_secret(self):
        return self.__secret

    def show_table(self):
        return self.__detail

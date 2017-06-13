import random
from functools import reduce

SUPPORTED_SIZE = [5, 8]

class table:
    def __init__(self, nick_list):
        self.__size = len(nick_list)

        if not reduce(lambda res, num: res or self.__size == num, SUPPORTED_SIZE, False):
            raise ValueError('irc-sha now only support for 5 or 8 players!')
        else:
            self.__position = list(nick_list)
            random.shuffle(self.__position)   # random players' position

    def show_table(self):
        return self.__position

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

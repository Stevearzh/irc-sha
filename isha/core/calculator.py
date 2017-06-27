class calculator:
    def __init__(self, table):
        self.__table = table
        self.__nicks = list(map(lambda p: p.nick(), table.players()))

    def distance(self, nick_a=None, nick_b=None):
        try:
            pos_a = self.__nicks.index(nick_a)
            pos_b = self.__nicks.index(nick_b)
            [max, min] = [pos_a, pos_b] if pos_a > pos_b else [pos_b, pos_a]

            distance = max - min
            if distance > len(self.__nicks) / 2:
                distance = len(self.__nicks) - distance
            return distance

        except Exception as e:
            return 'NaN'

    def damage(self, source_who, target_who):
        pass

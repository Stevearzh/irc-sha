class player:
    def __init__(self, nick):
        self.__nick   = nick   # player's nick in irc
        self.__alive  = True
        self.__max_hp = 0
        self.__hp     = 0
        self.__seat   = -1
        self.__cards  = []

    def get_nick(self):
        return self.__nick

    def change_nick(self, nick):
        self.__nick = nick

    def is_alive(self):
        return self.__alive

    def set_alive(self):
        self.__alive = True

    def is_dead(self):
        return not(self.__alive)

    def set_dead(self):
        self.__alive = False

    def get_max_hp(self):
        return self.__max_hp

    def change_max_hp(self, value):
        self.__max_hp = value

    def get_hp(self):
        return self.__hp

    def set_initial_hp(self, value):
        self.change_max_hp(value)
        self.__hp = value

    def encrease_hp(self):
        if self.__hp < self.__max_hp:
            self.__hp += 1

    def decrease_hp(self, value):
        self.__hp -= value

    def set_seat(self, position):
        self.__position = position

    def get_seat(self):
        return self.__position

    def get_card(self, card):
        self.__cards.append(card)

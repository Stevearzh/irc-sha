from isha.core.card import card
from isha.dict.card import CARD_TYPE, CARD_NAME
from isha.dict.status import STATUS

class sha(card):
    def __init__(self, suit, point):
        card.__init__(self, suit=suit, type=CARD_TYPE['basic'], point=point,
            name=CARD_NAME['sha'], effect=self.__effect, need_target=True)

    def __effect(self, player):
        # player.change_status(STATUS['being_sha'])
        pass   # should use fsm here

class shan(card):
    def __init__(self, suit, point):
        card.__init__(self, suit=suit, type=CARD_TYPE['basic'], point=point,
            name=CARD_NAME['shan'], effect=self.__effect)

    def __effect(self, player):
        pass

class peach(card):
    def __init__(self, suit, point):
        card.__init__(self, suit=suit, type=CARD_TYPE['basic'], point=point,
            name=CARD_NAME['peach'], effect=self.__effect)

    def __effect(self, player):
        if player.increase_hp():
            return '{} recovered 1 hp'.format(player.nick())

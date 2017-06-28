from isha.core.card import card
from isha.dict.card import CARD_TYPE, CARD_NAME

class sha(card):
    effect = 'become_sha_target'

    def __init__(self, suit, point):
        card.__init__(self, suit=suit, type=CARD_TYPE['basic'], point=point,
            name=CARD_NAME['sha'], effect=self.__effect, need_target=True)

    def __effect(self, player):
        eval('player.' + sha.effect + '()')

class shan(card):
    effect = 'shan_used'

    def __init__(self, suit, point):
        card.__init__(self, suit=suit, type=CARD_TYPE['basic'], point=point,
            name=CARD_NAME['shan'], effect=self.__effect)

    def __effect(self, player):
        eval('player.' + shan.effect + '()')

class peach(card):
    def __init__(self, suit, point):
        card.__init__(self, suit=suit, type=CARD_TYPE['basic'], point=point,
            name=CARD_NAME['peach'], effect=self.__effect)

    def __effect(self, player):
        if player.increase_hp():
            return '{} recovered 1 hp'.format(player.nick())

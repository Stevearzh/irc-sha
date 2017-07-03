from isha.core.card import card
from isha.dict.card import CARD_TYPE, CARD_NAME

class sha(card):
    effect = 'become_sha_target'
    passive_effect = 'sha_used'

    def __init__(self, suit, point):
        card.__init__(self, suit=suit, type=CARD_TYPE['basic'], point=point,
                      name=CARD_NAME['sha'], trigger=self.__trigger,
                      effect=self.__effect, need_target=True,
                      could_use_judge=self.__could_use_judge)

    def __could_use_judge(self, from_whom, to_whom, passive=False):
        if not passive:
            return True
        else:
            return True   # should judge if could use here

    def __trigger(self, player, passive=False):
        if not passive:
            return eval('player.' + sha.effect + '()')
        else:
            return True   # player response sha here

    def __effect(self, player):
        if not self.__passive:
            result = {
                'goal': 'damage',
                'value': 1,
                'func': player.decrease_hp
            }
        else:
            result = {
                'goal': 'response',
                'func': eval('player.' + sha.passive_effect)
            }
        return result

class shan(card):
    effect = 'shan_used'

    def __init__(self, suit, point):
        card.__init__(self, suit=suit, type=CARD_TYPE['basic'], point=point,
                      name=CARD_NAME['shan'], trigger=self.__trigger,
                      effect=self.__effect, could_use_judge=self.__could_use_judge)

    def __could_use_judge(self, from_whom, to_whom):
        return True

    def __trigger(self, player):
        return True

    def __effect(self, player):
        return {
            'func': eval('player.' + shan.effect)
        }

class peach(card):
    def __init__(self, suit, point):
        card.__init__(self, suit=suit, type=CARD_TYPE['basic'], point=point,
                      name=CARD_NAME['peach'], trigger=self.__trigger,
                      effect=self.__effect， could_use_judge=self.__could_use_judge)

    def __could_use_judge(self, from_whom, to_whom, passive=False):
        if not passive:
            return True
        else:
            return True # should judge could use peach to himself/herself

    def __trigger(self, player, passive=False):
        return True

    def __effect(self, player):
        if player.increase_hp():
            return '{} recovered 1 hp'.format(player.nick())

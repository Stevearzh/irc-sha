from isha.core.card import card
from isha.dict.card import CARD_TYPE, CARD_NAME

class sha(card):
    effect = 'become_sha_target'
    passive_effect = 'sha_used'

    def __init__(self, suit, point, passive=False):
        card.__init__(self, suit=suit, type=CARD_TYPE['basic'], point=point,
                      name=CARD_NAME['sha'], trigger=self.__trigger,
                      effect=self.__effect, need_target=True,
                      could_use_judge=self.__could_use_judge)
        self.__passive = passive

    def __could_use_judge(self, from_whom, to_whom):
        return True

    def __trigger(self, player):
        if not self.__passive:
            return eval('player.' + sha.effect + '()')
        else:
            return True

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
        self.__passive = True

    def __could_use_judge(self, from_whom, to_whom):
        return True

    def __trigger(self, player):
        return True

    def __effect(self, player):
        return {
            'func': eval('player.' + shan.effect)
        }

class peach(card):
    def __init__(self, suit, point, passive=False):
        card.__init__(self, suit=suit, type=CARD_TYPE['basic'], point=point,
                      name=CARD_NAME['peach'], trigger=self.__trigger,
                      effect=self.__effect， could_use_judge=self.__could_use_judge)
        self.__passive = passive

    def __could_use_judge(self, from_whom, to_whom):
        return True

    def __trigger(self, player):
        return True

    def __effect(self, player):
        if player.increase_hp():
            return '{} recovered 1 hp'.format(player.nick())

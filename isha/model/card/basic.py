from isha.core.card import card
from isha.dict.card import CARD_TYPE, CARD_NAME

class sha(card):
    def __init__(self, suit, point):
        card.__init__(self, suit=suit, type=CARD_TYPE['basic'], point=point, name=CARD_NAME['sha'])

class shan(card):
    def __init__(self, suit, point):
        card.__init__(self, suit=suit, type=CARD_TYPE['basic'], point=point, name=CARD_NAME['shan'])

class peach(card):
    def __init__(self, suit, point):
        card.__init__(self, suit=suit, type=CARD_TYPE['basic'], point=point, name=CARD_NAME['peach'])

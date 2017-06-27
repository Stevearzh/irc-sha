from isha.model.card.basic import sha, shan, peach
from isha.dict.card import CARD_TYPE

def card_parser(table, card, from_whom, to_whom=None):
    if to_whom:
        card(to_whom)
    elif not card.type() == CARD_TYPE['trick']:
        card(from_whom)

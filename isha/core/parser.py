from isha.model.card.basic import sha, shan, peach
from isha.dict.card import CARD_TYPE

def card_parser(table, card, from_whom, to_whom=None):
    if not card.could_use(from_whom, to_whom):
        from_whom.get_card(card)   # return card to player
        return False

    table.using_card(card)

    if to_whom:
        dest = to_whom
    elif not card.type() == CARD_TYPE['trick']:
        dest = from_whom

    card(dest)

    # wait for target response
    # if not dest == from_whom
    #   yield ...

    # damage calculate (if need)

    # drop card, etc.

CARD_SUIT = {
    'no_suit': 'no_suit',
    'spade': '♠',
    'heart': '♥',
    'club': '♣',
    'diamond': '♦',
    'unknown': 'unknown'
}

CARD_COLOR = {
    'no_color': 'no_color',
    'red': 'red',
    'black': 'black',
    'unknown': 'unknown'
}

CARD_TYPE = {
    'basic': 'basic',
    'trick': 'trick',
    'equip': 'equip',
    'unknown': 'unknown'
}

class card:
    def __init__(self, suit=CARD_SUIT['unknown'], color=CARD_COLOR['unknown'], type=CARD_TYPE['unknown'], point=0):
        self.__suit = suit
        self.__color = color
        self.__type = type
        self.__point = point

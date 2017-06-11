SUIT = {
    'no_suit': 'no_suit',
    'spade': '♠',
    'heart': '♥',
    'club': '♣',
    'diamond': '♦',
    'unknown': None
}

COLOR = {
    'no_color': 'no_color',
    'red': 'red',
    'black': 'black',
    'unknown': None
}

TYPE = {
    'basic': 'basic',
    'trick': 'trick',
    'equip': 'equip',
    'unknown': None
}

class card:
    def __init__(self, suit=SUIT['unknown'], color=COLOR['unknown'], type=TYPE['unknown'], point=0):
        self.__suit = suit
        self.__color = color
        self.__type = type
        self.__point = point

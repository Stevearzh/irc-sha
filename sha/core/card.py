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
    def __init__(self, suit=CARD_SUIT['unknown'], color=CARD_COLOR['unknown'], type=CARD_TYPE['unknown'], point=0, name=None):
        self.__suit  = suit
        self.__color = color
        self.__type  = type
        self.__point = str(point)
        self.__name  = name

        if not self.__color == CARD_COLOR['no_color']:
            self.__judge_color()

    def __judge_color(self):
        try:
            self.__color = {
                'spade': 'black',
                'heart': 'red',
                'club': 'black',
                'diamond': 'red'
            }[self.__suit]
        except Exception as e:
            pass

    def suit(self):
        return CARD_SUIT[self.__suit]

    def color(self):
        return self.__color

    def point(self):
        return self.__point

    def name(self):
        return self.__name

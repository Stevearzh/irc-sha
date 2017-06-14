from sha.dict.card import CARD_SUIT, CARD_COLOR, CARD_TYPE

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
            self.__color = list(filter(lambda r: r['suit'] == self.__suit, [
                { 'suit': CARD_SUIT['spade'], 'color': CARD_COLOR['black'] },
                { 'suit': CARD_SUIT['heart'], 'color': CARD_COLOR['red'] },
                { 'suit': CARD_SUIT['club'], 'color': CARD_COLOR['black'] },
                { 'suit': CARD_SUIT['diamond'], 'color': CARD_COLOR['red'] }
            ]))[0]['color']
        except Exception as e:
            pass

    def suit(self):
        return self.__suit

    def color(self):
        return self.__color

    def point(self):
        return self.__point

    def name(self):
        return self.__name

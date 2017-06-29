from isha.dict.card import CARD_SUIT, CARD_COLOR, CARD_TYPE

class card:
    def __init__(self, suit=CARD_SUIT['unknown'], color=CARD_COLOR['unknown'],
                 type=CARD_TYPE['unknown'], point=0, name=None, trigger = None,
                 effect=None, need_target=False, could_use_judge=None):
        self.__suit    = suit
        self.__color   = color
        self.__type    = type
        self.__point   = str(point)
        self.__name    = name
        self.__ndt     = need_target
        self.__trigger = trigger
        self.__effect  = effect
        self.__cujudge = could_use_judge

        if not self.__color == CARD_COLOR['no_color']:
            self.__color = self.__judge_color(self.__suit)

    def __judge_color(self, suit):
        try:
             return list(filter(lambda r: r['suit'] == suit, [
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

    def type(self):
        return self.__type

    def need_target(self):
        return self.__ndt

    def __call__(self, *args, **kwargs):
        self.__trigger(*args, **kwargs)

    def effect(self, *args, **kwargs):
        self.__effect(*args, **kwargs)

    def could_use(self, *args, **kwargs):
        return self.__cujudge(*args, **kwargs)

def explain_card_assign():
    return '，'.join([
        '使用 <花色><点数><名字> 来选取你要出的牌',
        '使用 S 来表示花色黑桃 ♠',
        '使用 H 来表示花色红桃 ♥',
        '使用 C 来表示花色梅花 ♣',
        '使用 D 来表示花色方片 ♦',
        '例如：DK杀、d6闪、S9杀、h10杀、dq桃'
    ])

def assign_card(string, stack):
    suit = {
        'S': CARD_SUIT['spade'],
        'H': CARD_SUIT['heart'],
        'C': CARD_SUIT['club'],
        'D': CARD_SUIT['diamond']
    }[string[0].upper()]

    if string[1] == '1':
        point = string[1: 3]
        name  = string[3:]
    else:
        point = string[1].upper()
        name  = string[2:]

    result = list(filter(lambda card: card.suit() == suit and card.point() == point and card.name() == name, stack))
    if len(result):
        return result[0]
    else:
        return None

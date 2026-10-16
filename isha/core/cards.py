"""卡牌数据模型与文本选牌协议（"h10杀" 风格）。"""

from dataclasses import dataclass

from isha.dict.card import CARD_COLOR, CARD_SUIT, CARD_TYPE

SUIT_LETTERS = {
    'S': CARD_SUIT['spade'],
    'H': CARD_SUIT['heart'],
    'C': CARD_SUIT['club'],
    'D': CARD_SUIT['diamond'],
}

SUIT_COLORS = {
    CARD_SUIT['spade']: CARD_COLOR['black'],
    CARD_SUIT['heart']: CARD_COLOR['red'],
    CARD_SUIT['club']: CARD_COLOR['black'],
    CARD_SUIT['diamond']: CARD_COLOR['red'],
}


@dataclass(frozen=True)
class Card:
    """一张牌的实例。cid 在整副牌堆中唯一（同花色同点数同名的牌有多张）。

    spec：牌名括号里的规格，如 青龙偃月刀（3）→ '3'（武器范围），
    绝影（+1）→ '+1'（马匹修正）；无括号则为 ''。
    """

    cid: int
    suit: str
    point: str
    name: str
    type: str = CARD_TYPE['unknown']
    color: str = CARD_COLOR['unknown']
    spec: str = ''

    @property
    def label(self) -> str:
        return f'{self.suit}{self.point}{self.name}'

    @property
    def detail(self) -> str:
        """带规格的展示名：♠5丈八蛇矛（3）、♥K绝影（+1）。"""
        return f'{self.label}（{self.spec}）' if self.spec else self.label


def make_card(cid: int, suit: str, point: str, name: str,
              type: str = CARD_TYPE['unknown'], spec: str = '') -> Card:
    return Card(cid=cid, suit=suit, point=str(point), name=name, type=type,
                color=SUIT_COLORS.get(suit, CARD_COLOR['unknown']), spec=spec)


def explain_card_assign() -> str:
    return '，'.join([
        '使用 <花色><点数><名字> 来选取你要出的牌',
        '使用 S 来表示花色黑桃 ♠',
        '使用 H 来表示花色红桃 ♥',
        '使用 C 来表示花色梅花 ♣',
        '使用 D 来表示花色方片 ♦',
        '例如：DK杀、d6闪、S9杀、h10杀、dq桃',
        '名字可省略（花色+点数在单副牌中唯一），如 H8 即 ♥8无中生有',
    ])


def parse_ref(text: str) -> tuple[str, str, str] | None:
    """解析文本选牌引用 -> (suit, point, name)；不合法返回 None。

    名字可省略（如 'H8'），此时 name 为 ''。
    """
    text = text.strip()
    if len(text) < 2:
        return None
    suit = SUIT_LETTERS.get(text[0].upper())
    if suit is None:
        return None
    if text[1] == '1':   # 点数为 10 时用两位
        point, name = '10', text[3:]
    else:
        point, name = text[1].upper(), text[2:]
    return suit, point, name


def find_card(text: str, hand: list[Card]) -> Card | None:
    """按文本选牌协议从 hand 中找到第一张匹配的牌，找不到返回 None。

    名字省略时只按花色+点数匹配（单副牌中该组合唯一）；
    带名字则要求花色+点数+名字精确匹配。
    """
    ref = parse_ref(text)
    if ref is None:
        return None
    suit, point, name = ref
    for card in hand:
        if card.suit == suit and card.point == point \
                and (not name or card.name == name):
            return card
    return None

"""测试共享工具：构造确定性牌堆与引擎。

牌堆布局：20 张按座位发牌（每人 4 张），之后依次为牌堆顶。
例如 5 人局中 rest[0..1] 是主公第一回合摸的牌，rest[2] 起依次被消耗。
"""

import random

from isha.core.actions import Pass, PlayCards
from isha.core.cards import make_card
from isha.core.engine import Engine
from isha.dict.card import CARD_NAME, CARD_SUIT
from isha.dict.identity import IDENTITY
from isha.card import DEFAULT_RULES

SHA = CARD_NAME['sha']
SHAN = CARD_NAME['shan']
PEACH = CARD_NAME['peach']
S = CARD_SUIT['spade']
H = CARD_SUIT['heart']

NICKS5 = ['a', 'b', 'c', 'd', 'e']
IDS5 = [IDENTITY['king'], IDENTITY['rebel'], IDENTITY['rebel'],
        IDENTITY['minister'], IDENTITY['traitor']]


WEAPON_SPECS = {
    CARD_NAME['zhuge']: '1', CARD_NAME['gender_sword']: '2',
    CARD_NAME['qinggang']: '2', CARD_NAME['qinglong']: '3',
    CARD_NAME['zhangba']: '3', CARD_NAME['guanshi']: '3',
    CARD_NAME['fangtian']: '4', CARD_NAME['qilin']: '5',
    CARD_NAME['icesword']: '2',
}


def make_deck(hands, rest):
    """hands[i] 是第 i 个座位摸到的 4 张；rest 为剩余牌堆（栈顶在前）。"""
    names = [name for hand in hands for name in hand] + list(rest)
    return [make_card(i, S, 'A', name, spec=WEAPON_SPECS.get(name, ''))
            for i, name in enumerate(names)]


def start_engine(hands, rest=None, ids=IDS5, nicks=NICKS5):
    deck = make_deck(hands, ['杀'] * 40 if rest is None else rest)
    eng = Engine(list(zip(nicks, ids)), deck, DEFAULT_RULES, random.Random(1))
    eng.drain_effects()
    return eng


def sha_hands():
    return [[SHA] * 4 for _ in range(5)]


def cid(eng, nick, name, i=0):
    return [c.cid for c in eng.player(nick).hand if c.name == name][i]


def kinds(effects):
    return [e.kind for e in effects]


def play_card(eng, source, name, target=None, i=0):
    return eng.apply(PlayCards(source, (cid(eng, source, name, i),), target))


def play_sha(eng, source, target, i=0):
    return play_card(eng, source, SHA, target, i)


def pass_play_and_discard(eng):
    """当前玩家结束出牌阶段，并用默认动作完成弃牌。返回过程中的 effects。"""
    player = eng.pending.player
    effects = eng.apply(Pass(player))
    while eng.pending and eng.pending.player == player \
            and eng.pending.kind == 'discard':
        effects += eng.apply(eng.pending.default)
    return effects

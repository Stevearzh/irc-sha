"""游戏前端层：对局组装入口，及 CLI / Web / 渲染前端。

new_game 组装一局游戏：建牌堆 → 洗牌 → 分身份 → 主公坐首位。
"""

import random

from isha.card import DEFAULT_CARD_TYPES, DEFAULT_RULES
from isha.core.deck import build_deck
from isha.core.engine import Engine
from isha.core.identity import gen_id_list
from isha.dict.identity import IDENTITY

__all__ = ['new_game']


def new_game(nicks: list[str], card_path: str = 'package/card/',
             packs: tuple[str, ...] = ('common',), seed=None,
             rules: dict | None = None) -> Engine:
    """组装一局游戏：建牌堆 → 洗牌 → 分身份 → 主公坐首位。"""
    rules = rules or DEFAULT_RULES
    rng = random.Random(seed)
    deck = build_deck(card_path, list(packs), set(rules), rng, DEFAULT_CARD_TYPES)

    order = list(nicks)
    rng.shuffle(order)
    players = list(zip(order, gen_id_list(len(order), rng)))
    king_at = next(i for i, (_, ident) in enumerate(players)
                   if ident == IDENTITY['king'])
    players = players[king_at:] + players[:king_at]

    return Engine(players, deck, rules, rng)

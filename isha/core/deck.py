"""牌堆构建：从 csv 卡包读牌，按已注册的牌名过滤，生成带唯一 cid 的 Card。

csv 中装备牌名带规格括号（如 青龙偃月刀（3）、绝影（+1)），
加载时拆分为 name + spec。
"""

import csv
import random
import re

from isha.dict.card import CARD_SUIT, CARD_TYPE

from .cards import make_card

SPEC_RE = re.compile(r'^(?P<name>.*?)（(?P<spec>.*?)）$')


def load_pack(source: str) -> list[dict]:
    result = []
    with open(source, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            name, spec = row['name'], ''
            m = SPEC_RE.match(name)
            if m:
                name, spec = m.group('name'), m.group('spec')
            result.append({'suit': CARD_SUIT[row['suit']], 'point': row['point'],
                           'name': name, 'spec': spec})
    return result


def build_deck(card_path: str, packs: list[str], allowed_names: set[str],
               rng: random.Random, card_types: dict[str, str] | None = None) -> list:
    """读取卡包、按 allowed_names 过滤、洗牌后返回牌堆（栈顶在列表头部）。"""
    card_types = card_types or {}
    models = []
    for pack in packs:
        models.extend(load_pack(card_path + pack + '.csv'))

    deck = []
    for cid, model in enumerate(m for m in models if m['name'] in allowed_names):
        deck.append(make_card(cid, type=card_types.get(model['name'], CARD_TYPE['basic']),
                              **model))

    rng.shuffle(deck)
    return deck

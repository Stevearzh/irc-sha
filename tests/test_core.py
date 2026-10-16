import random

import pytest

from isha.core.calculator import cyclic_distance, seat_distance
from isha.core.cards import find_card, make_card
from isha.core.deck import build_deck
from isha.core.identity import gen_id_list
from isha.dict.card import CARD_SUIT
from isha.dict.identity import IDENTITY

S = CARD_SUIT['spade']
H = CARD_SUIT['heart']
D = CARD_SUIT['diamond']


# ---------- 选牌协议 ----------

def hand():
    return [
        make_card(0, H, '10', '杀'),
        make_card(1, D, '6', '闪'),
        make_card(2, S, '9', '杀'),
        make_card(3, S, '9', '杀'),   # 同花色同点数同名：cid 区分实例
    ]


def test_find_card():
    assert find_card('h10杀', hand()).cid == 0
    assert find_card('D6闪', hand()).cid == 1
    assert find_card('s9杀', hand()).cid == 2


def test_find_card_name_omitted():
    """名字可省略：按花色+点数匹配。"""
    assert find_card('h10', hand()).cid == 0
    assert find_card('h1', hand()).cid == 0   # '1' 即 10 的前缀写法
    assert find_card('D6', hand()).cid == 1
    assert find_card('s9', hand()).cid == 2   # 同花色同点数取第一张


def test_find_card_miss():
    assert find_card('h9杀', hand()) is None
    assert find_card('h9', hand()) is None
    assert find_card('x9杀', hand()) is None
    assert find_card('h', hand()) is None
    assert find_card('', hand()) is None


def test_card_detail():
    assert make_card(0, S, '5', '丈八蛇矛', spec='3').detail == '♠5丈八蛇矛（3）'
    assert make_card(1, H, 'K', '绝影', spec='+1').detail == '♥K绝影（+1）'
    assert make_card(2, S, 'A', '杀').detail == '♠A杀'


# ---------- 距离 ----------

def test_cyclic_distance():
    assert cyclic_distance(0, 1, 5) == 1
    assert cyclic_distance(0, 4, 5) == 1
    assert cyclic_distance(0, 2, 5) == 2


def test_seat_distance_nan():
    assert seat_distance(['a', 'b', 'c'], 'a', 'c') == 1
    assert seat_distance(['a', 'b', 'c'], 'a', 'x') == 'NaN'


# ---------- 身份 ----------

def test_gen_id_list():
    ids = gen_id_list(5, random.Random(1))
    assert sorted(ids) == sorted([
        IDENTITY['king'], IDENTITY['minister'],
        IDENTITY['rebel'], IDENTITY['rebel'], IDENTITY['traitor']])
    assert len(gen_id_list(8, random.Random(1))) == 8
    with pytest.raises(ValueError):
        gen_id_list(6)


# ---------- 牌堆构建 ----------

def test_build_deck_filters_unregistered():
    deck = build_deck('package/card/', ['common'], {'杀', '闪', '桃'},
                      random.Random(1))
    assert len(deck) == 30 + 15 + 8
    assert len({c.cid for c in deck}) == len(deck)   # cid 唯一
    assert all(c.name in {'杀', '闪', '桃'} for c in deck)
    assert all(c.color for c in deck)


def test_build_deck_ex_pack():
    """EX 包 4 张全部有规则实现：启用后牌堆 108 张。"""
    from isha.card import DEFAULT_CARD_TYPES, DEFAULT_RULES
    deck = build_deck('package/card/', ['common', 'ex'], set(DEFAULT_RULES),
                      random.Random(1), DEFAULT_CARD_TYPES)
    assert len(deck) == 104 + 4
    names = {c.name for c in deck}
    assert {'寒冰剑', '仁王盾', '闪电', '无懈可击'} <= names
    assert next(c for c in deck if c.name == '寒冰剑').spec == '2'

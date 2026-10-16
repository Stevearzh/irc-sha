"""装备与距离修正测试：武器特效、八卦阵、马匹、借刀杀人、装备区拆顺。"""

import pytest

from isha.core.actions import DiscardCards, Pass, PlayCards
from isha.core.cards import make_card
from isha.core.engine import IllegalAction
from isha.dict.card import CARD_NAME, CARD_SUIT

from helpers import (H, PEACH, SHA, SHAN, cid, kinds, pass_play_and_discard,
                     play_card, play_sha, sha_hands, start_engine)

S = CARD_SUIT['spade']
ZHUGE = CARD_NAME['zhuge']
QINGGANG = CARD_NAME['qinggang']
QINGLONG = CARD_NAME['qinglong']
ZHANGBA = CARD_NAME['zhangba']
GUANSHI = CARD_NAME['guanshi']
QILIN = CARD_NAME['qilin']
FANGTIAN = CARD_NAME['fangtian']
BAGUA = CARD_NAME['bagua']
RENWANG = CARD_NAME['renwang']
ICESWORD = CARD_NAME['icesword']
BORROW = CARD_NAME['borrow']


def equip(cid, name, spec=''):
    return make_card(cid, S, '5', name, spec=spec)


def rearm(eng, nick, name, spec, slot):
    """白盒：直接给玩家装装备，并重建出牌询问（选项在挂起时固化）。"""
    setattr(eng.player(nick), slot, equip(900, name, spec))
    if eng.pending and eng.pending.kind == 'play':
        eng.pending = eng._play_ask(eng.player(eng.pending.player))


# ---------- 距离与范围 ----------

def test_weapon_range_extends_sha():
    eng = start_engine(sha_hands())
    rearm(eng, 'a', QINGLONG, '3', 'weapon')
    play_sha(eng, 'a', 'c')               # a-c 距离 2 ≤ 青龙偃月刀 3


def test_minus_horse_shortens_distance():
    eng = start_engine(sha_hands())
    rearm(eng, 'a', '赤兔', '-1', 'minus_horse')
    assert eng.distance('a', 'c') == 1    # 2 - 1
    play_sha(eng, 'a', 'c')


def test_plus_horse_lengthens_distance():
    eng = start_engine(sha_hands())
    rearm(eng, 'c', '绝影', '+1', 'plus_horse')
    assert eng.distance('a', 'c') == 3    # 2 + 1
    with pytest.raises(IllegalAction):
        play_sha(eng, 'a', 'c')           # 超出攻击范围
    play_sha(eng, 'a', 'b')               # b 仍可达


def test_equip_replaces_old():
    hands = sha_hands()
    hands[0] = [QINGLONG, ZHUGE, SHA, SHA]
    eng = start_engine(hands)
    old_cid = cid(eng, 'a', QINGLONG)
    play_card(eng, 'a', QINGLONG)
    assert eng.king.weapon.spec == '3'
    effects = play_card(eng, 'a', ZHUGE)
    assert eng.king.weapon.spec == '1'
    assert 'unequip' in kinds(effects)
    assert any(c.cid == old_cid for c in eng.discard_pile)


# ---------- 武器特效 ----------

def test_zhuge_unlimited_sha():
    eng = start_engine(sha_hands())
    rearm(eng, 'a', ZHUGE, '1', 'weapon')
    play_sha(eng, 'a', 'b')
    play_sha(eng, 'a', 'b', i=0)          # 第二张杀不受限制
    assert eng.player('b').hp == 2


def test_qinglong_chase():
    hands = sha_hands()
    hands[1] = [SHAN, SHA, SHA, SHA]
    eng = start_engine(hands)
    rearm(eng, 'a', QINGLONG, '3', 'weapon')
    play_sha(eng, 'a', 'b')
    eng.apply(PlayCards('b', (cid(eng, 'b', SHAN),)))   # b 闪避
    assert eng.pending.kind == 'chase' and eng.pending.player == 'a'
    eng.apply(PlayCards('a', (cid(eng, 'a', SHA),)))    # 追杀
    assert eng.player('b').hp == 3        # 追杀命中（b 已无闪）


def test_guanshi_force_hit():
    hands = sha_hands()
    hands[1] = [SHAN, SHA, SHA, SHA]
    eng = start_engine(hands)
    rearm(eng, 'a', GUANSHI, '3', 'weapon')
    play_sha(eng, 'a', 'b')
    eng.apply(PlayCards('b', (cid(eng, 'b', SHAN),)))
    assert eng.pending.kind == 'guanshi' and eng.pending.player == 'a'
    two = tuple(c.cid for c in eng.king.hand[:2])
    effects = eng.apply(DiscardCards('a', two))
    assert 'guanshi' in kinds(effects)
    assert eng.player('b').hp == 3        # 强命成功
    assert len(eng.king.hand) == 5 - 2


def test_guanshi_pass_no_hit():
    hands = sha_hands()
    hands[1] = [SHAN, SHA, SHA, SHA]
    eng = start_engine(hands)
    rearm(eng, 'a', GUANSHI, '3', 'weapon')
    play_sha(eng, 'a', 'b')
    eng.apply(PlayCards('b', (cid(eng, 'b', SHAN),)))
    eng.apply(Pass('a'))                  # 不强制命中
    assert eng.player('b').hp == 4


def test_qilin_shoots_horse():
    eng = start_engine(sha_hands())
    rearm(eng, 'a', QILIN, '5', 'weapon')
    eng.player('b').plus_horse = equip(901, '绝影', '+1')
    play_sha(eng, 'a', 'b')               # b 无闪直接命中
    assert eng.pending.kind == 'qilin' and eng.pending.player == 'a'
    horse_cid = eng.pending.data['cards'][0][0]
    effects = eng.apply(PlayCards('a', (horse_cid,)))
    assert 'horse_shot' in kinds(effects)
    assert eng.player('b').plus_horse is None


def test_zhangba_two_cards_as_sha():
    eng = start_engine(sha_hands())
    rearm(eng, 'a', ZHANGBA, '3', 'weapon')
    assert eng.pending.data['zhangba']
    c1, c2 = eng.king.hand[0].cid, eng.king.hand[1].cid
    eng.apply(PlayCards('a', (c1, c2), 'c'))   # 丈八范围 3，可及 c
    assert eng.player('c').hp == 3        # 无闪命中
    assert eng.king.used_sha


def test_zhangba_rejects_bad_input():
    eng = start_engine(sha_hands())
    rearm(eng, 'a', ZHANGBA, '3', 'weapon')
    c1 = eng.king.hand[0].cid
    with pytest.raises(IllegalAction):
        eng.apply(PlayCards('a', (c1, c1), 'b'))       # 同一张牌两次
    with pytest.raises(IllegalAction):
        eng.apply(PlayCards('a', (c1, eng.king.hand[1].cid,
                                  eng.king.hand[2].cid), 'b'))   # 三张牌


# ---------- 八卦阵 ----------

def test_bagua_red_dodges():
    eng = start_engine(sha_hands())
    rearm(eng, 'b', BAGUA, '', 'armor')
    eng.deck[0] = make_card(998, H, '7', SHA)   # 判定牌：红
    play_sha(eng, 'a', 'b')
    assert eng.pending.data['armor']
    effects = eng.apply(PlayCards('b', ()))     # 八卦阵判定
    assert 'dodge' in kinds(effects)
    assert eng.player('b').hp == 4


def test_bagua_black_needs_shan():
    hands = sha_hands()
    hands[1] = [SHAN, SHA, SHA, SHA]
    eng = start_engine(hands)
    rearm(eng, 'b', BAGUA, '', 'armor')
    eng.deck[0] = make_card(998, S, '7', SHA)   # 判定牌：黑
    play_sha(eng, 'a', 'b')
    eng.apply(PlayCards('b', ()))               # 判定失败
    assert eng.pending.kind == 'respond_sha'
    assert not eng.pending.data['armor']        # 本次响应不能再判
    eng.apply(PlayCards('b', (cid(eng, 'b', SHAN),)))
    assert eng.player('b').hp == 4


def test_qinggang_ignores_bagua():
    hands = sha_hands()
    hands[1] = [SHAN, SHA, SHA, SHA]
    eng = start_engine(hands)
    rearm(eng, 'a', QINGGANG, '2', 'weapon')
    eng.player('b').armor = equip(901, BAGUA)
    play_sha(eng, 'a', 'b')
    assert not eng.pending.data['armor']        # 八卦阵被无视
    eng.apply(Pass('b'))
    assert eng.player('b').hp == 3


# ---------- 方天画戟 ----------

def _fangtian_setup():
    """a 装备方天画戟，且杀是最后一张手牌（满足多目标条件）。"""
    eng = start_engine(sha_hands())
    rearm(eng, 'a', FANGTIAN, '4', 'weapon')
    a = eng.king
    a.hand = a.hand[:1]
    eng.pending = eng._play_ask(a)   # multi 选项在挂起时固化，重建出牌询问
    return eng


def test_fangtian_multi_target():
    eng = _fangtian_setup()
    a = eng.king
    sha_cid = a.hand[0].cid
    assert eng.pending.data['multi'] == {sha_cid: 3}
    effects = eng.apply(PlayCards('a', (sha_cid,), ['b', 'c', 'd']))
    used = next(e for e in effects if e.kind == 'card_used')
    assert used.data['target'] == 'b、c、d'
    assert not a.hand
    for nick in ('b', 'c', 'd'):       # 三人皆无闪，各受 1 点伤害
        assert eng.player(nick).hp == 3


def test_fangtian_resolves_in_seat_order():
    hands = sha_hands()
    hands[1] = [SHAN, SHA, SHA, SHA]
    hands[2] = [SHAN, SHA, SHA, SHA]
    eng = start_engine(hands)
    rearm(eng, 'a', FANGTIAN, '4', 'weapon')
    a = eng.king
    a.hand = a.hand[:1]
    eng.pending = eng._play_ask(a)
    # 乱序指定 c、b，仍按座次先 b 后 c 逐个响应
    eng.apply(PlayCards('a', (a.hand[0].cid,), ['c', 'b']))
    assert eng.pending.kind == 'respond_sha' and eng.pending.player == 'b'
    eng.apply(PlayCards('b', (cid(eng, 'b', SHAN),)))
    assert eng.pending.kind == 'respond_sha' and eng.pending.player == 'c'
    eng.apply(Pass('c'))
    assert eng.player('b').hp == 4 and eng.player('c').hp == 3


def test_fangtian_needs_last_hand_card():
    eng = start_engine(sha_hands())
    rearm(eng, 'a', FANGTIAN, '4', 'weapon')   # 手牌 4 张，杀不是最后一张
    assert not eng.pending.data['multi']
    sha_cid = eng.king.hand[0].cid
    with pytest.raises(IllegalAction):
        eng.apply(PlayCards('a', (sha_cid,), ['b', 'c']))
    eng.apply(PlayCards('a', (sha_cid,), 'b'))   # 单目标不受影响
    assert eng.player('b').hp == 3


def test_fangtian_multi_validation():
    eng = _fangtian_setup()
    sha_cid = eng.king.hand[0].cid
    with pytest.raises(IllegalAction):
        eng.apply(PlayCards('a', (sha_cid,), ['b', 'c', 'd', 'e']))  # 超过 3 名
    with pytest.raises(IllegalAction):
        eng.apply(PlayCards('a', (sha_cid,), ['b', 'b']))            # 重复目标
    with pytest.raises(IllegalAction):
        eng.apply(PlayCards('a', (sha_cid,), ['b', 'x']))            # 非法目标
    with pytest.raises(IllegalAction):
        eng.apply(PlayCards('a', (sha_cid,), []))                    # 空目标


# ---------- 仁王盾 ----------
def test_renwang_blocks_black_sha():
    eng = start_engine(sha_hands())             # helpers 牌堆全是黑桃（黑色）杀
    rearm(eng, 'b', RENWANG, '', 'armor')
    effects = play_sha(eng, 'a', 'b')
    assert 'renwang' in kinds(effects)
    assert eng.player('b').hp == 4
    assert eng.pending.kind == 'play'           # 无闪避窗口，直接回到 a 的出牌


def test_renwang_red_sha_works():
    hands = sha_hands()
    hands[1] = [SHAN, SHA, SHA, SHA]
    eng = start_engine(hands)
    rearm(eng, 'b', RENWANG, '', 'armor')
    a = eng.king
    a.hand[0] = make_card(a.hand[0].cid, H, '7', SHA)   # 红杀
    play_sha(eng, 'a', 'b')
    assert eng.pending.kind == 'respond_sha'    # 红色杀正常进入闪避窗口
    eng.apply(PlayCards('b', (cid(eng, 'b', SHAN),)))
    assert eng.player('b').hp == 4


def test_qinggang_beats_renwang():
    hands = sha_hands()
    hands[1] = [SHAN, SHA, SHA, SHA]
    eng = start_engine(hands)
    rearm(eng, 'a', QINGGANG, '2', 'weapon')
    eng.player('b').armor = equip(901, RENWANG)
    play_sha(eng, 'a', 'b')
    assert eng.pending.kind == 'respond_sha'    # 青釭剑无视防具
    eng.apply(Pass('b'))
    assert eng.player('b').hp == 3


def test_zhangba_black_pair_blocked_by_renwang():
    eng = start_engine(sha_hands())
    rearm(eng, 'a', ZHANGBA, '3', 'weapon')
    rearm(eng, 'b', RENWANG, '', 'armor')
    c1, c2 = eng.king.hand[0].cid, eng.king.hand[1].cid
    effects = eng.apply(PlayCards('a', (c1, c2), 'b'))  # 两张黑牌当杀 = 黑杀
    assert 'renwang' in kinds(effects)
    assert eng.player('b').hp == 4


def test_zhangba_mixed_pair_not_blocked():
    eng = start_engine(sha_hands())
    rearm(eng, 'a', ZHANGBA, '3', 'weapon')
    rearm(eng, 'b', RENWANG, '', 'armor')
    a = eng.king
    a.hand[1] = make_card(a.hand[1].cid, H, '7', SHA)   # 一黑一红 = 无色杀
    effects = eng.apply(PlayCards('a', (a.hand[0].cid, a.hand[1].cid), 'b'))
    assert 'renwang' not in kinds(effects)
    assert eng.player('b').hp == 3              # 无色杀不受仁王盾阻挡，b 无闪受伤


# ---------- 寒冰剑 ----------

def test_icesword_discards_two():
    eng = start_engine(sha_hands())
    rearm(eng, 'a', ICESWORD, '2', 'weapon')
    play_sha(eng, 'a', 'b')                     # b 无闪命中
    assert eng.pending.kind == 'icesword' and eng.pending.player == 'a'
    options = eng.pending.data['cards']
    assert all(label is None for _, label in options)   # 手牌暗选
    assert eng.pending.data['optional']
    eng.apply(PlayCards('a', (options[0][0],)))
    assert eng.pending.kind == 'icesword'       # 弃第二张
    assert not eng.pending.data['optional']
    effects = eng.apply(PlayCards('a', (eng.pending.data['cards'][0][0],)))
    assert 'icesword' in kinds(effects)
    b = eng.player('b')
    assert b.hp == 4 and len(b.hand) == 2       # 伤害被防止，改弃两张
    assert eng.pending.kind == 'play'


def test_icesword_pass_deals_damage():
    eng = start_engine(sha_hands())
    rearm(eng, 'a', ICESWORD, '2', 'weapon')
    play_sha(eng, 'a', 'b')
    eng.apply(Pass('a'))                        # 放弃寒冰剑特效
    assert eng.player('b').hp == 3


def test_icesword_can_take_equipment():
    eng = start_engine(sha_hands())
    rearm(eng, 'a', ICESWORD, '2', 'weapon')
    eng.player('b').weapon = equip(901, GUANSHI, '3')
    play_sha(eng, 'a', 'b')
    options = eng.pending.data['cards']
    weapon_opt = [o for o in options if o[1] and GUANSHI in o[1]]
    assert weapon_opt                           # 装备区明选
    eng.apply(PlayCards('a', (weapon_opt[0][0],)))
    assert eng.player('b').weapon is None
    assert any(c.cid == 901 for c in eng.discard_pile)
    eng.apply(PlayCards('a', (eng.pending.data['cards'][0][0],)))   # 第二张
    assert eng.player('b').hp == 4


def test_icesword_single_card():
    eng = start_engine(sha_hands())
    rearm(eng, 'a', ICESWORD, '2', 'weapon')
    b = eng.player('b')
    b.hand = b.hand[:1]
    play_sha(eng, 'a', 'b')
    effects = eng.apply(PlayCards('a', (eng.pending.data['cards'][0][0],)))
    assert 'icesword' in kinds(effects)
    assert b.hp == 4 and not b.hand             # 只有一张牌：弃完即止
    assert eng.pending.kind == 'play'           # 无第二次询问


def test_icesword_ignores_judgement():
    eng = start_engine(sha_hands())
    rearm(eng, 'a', ICESWORD, '2', 'weapon')
    b = eng.player('b')
    b.hand = []
    b.judgement.append(make_card(950, S, '6', CARD_NAME['contentment']))
    play_sha(eng, 'a', 'b')                     # 判定区不可选 → 无寒冰剑窗口
    assert b.hp == 3


# ---------- 借刀杀人 ----------

def _borrow_setup():
    hands = sha_hands()
    hands[0] = [BORROW, SHA, SHA, SHA]
    eng = start_engine(hands)
    eng.player('b').weapon = equip(900, QINGGANG, '2')
    eng.pending = eng._play_ask(eng.king)   # 白盒：装武器后重建出牌询问
    return eng


def test_borrow_sword_sha():
    eng = _borrow_setup()
    play_card(eng, 'a', BORROW, 'b')
    assert eng.pending.kind == 'choose_player' and eng.pending.player == 'a'
    assert set(eng.pending.data['targets']) == {'a', 'c', 'd', 'e'}
    eng.apply(PlayCards('a', (), 'c'))          # 指定 b 杀 c
    assert eng.pending.kind == 'borrow_sha' and eng.pending.player == 'b'
    eng.apply(PlayCards('b', (cid(eng, 'b', SHA),)))
    assert eng.player('c').hp == 3              # c 无闪被杀中
    assert eng.player('b').weapon is not None   # b 出杀，武器保留


def test_borrow_sword_give_weapon():
    eng = _borrow_setup()
    play_card(eng, 'a', BORROW, 'b')
    eng.apply(PlayCards('a', (), 'c'))
    effects = eng.apply(Pass('b'))              # b 不出杀 → 武器归 a
    assert 'weapon_gained' in kinds(effects)
    assert eng.player('b').weapon is None
    assert QINGGANG in [c.name for c in eng.king.hand]


def test_borrow_sword_needs_weapon():
    hands = sha_hands()
    hands[0] = [BORROW, SHA, SHA, SHA]
    eng = start_engine(hands)
    with pytest.raises(IllegalAction):
        play_card(eng, 'a', BORROW, 'b')   # 无人装备武器，借刀不可用


def _borrow_zhangba_setup(b_hand):
    """b 装备丈八蛇矛；a 借刀指定 b 杀 c 后，停在 b 的出杀响应窗口。"""
    hands = sha_hands()
    hands[0] = [BORROW, SHA, SHA, SHA]
    hands[1] = b_hand
    eng = start_engine(hands)
    eng.player('b').weapon = equip(900, ZHANGBA, '3')
    eng.pending = eng._play_ask(eng.king)   # 白盒：装武器后重建出牌询问
    play_card(eng, 'a', BORROW, 'b')
    eng.apply(PlayCards('a', (), 'c'))
    assert eng.pending.kind == 'borrow_sha' and eng.pending.player == 'b'
    return eng


def test_borrow_sword_zhangba_two_cards():
    """无杀但有丈八蛇矛且手牌 ≥2：可两张手牌当杀，武器保留。"""
    eng = _borrow_zhangba_setup([SHAN, SHAN, PEACH, SHAN])
    ask = eng.pending
    assert ask.data['zhangba'] and ask.data['cards'] == []   # 没有真杀可出
    c0, c1 = (c.cid for c in eng.player('b').hand[:2])
    effects = eng.apply(PlayCards('b', (c0, c1)))            # 两牌当杀
    assert eng.player('c').hp == 3                           # 虚拟杀命中
    assert eng.player('b').weapon is not None                # 出杀成功，武器保留
    assert 'weapon_gained' not in kinds(effects)


def test_borrow_sword_zhangba_decline():
    """有丈八蛇矛但选择不发动：武器照常交给借刀者。"""
    eng = _borrow_zhangba_setup([SHAN, SHAN, PEACH, SHAN])
    effects = eng.apply(Pass('b'))
    assert 'weapon_gained' in kinds(effects)
    assert eng.player('b').weapon is None
    assert ZHANGBA in [c.name for c in eng.king.hand]


def test_borrow_sword_zhangba_or_real_sha():
    """同时有杀和丈八蛇矛：出真杀或用两牌当杀均可。"""
    eng = _borrow_zhangba_setup([SHA, SHAN, PEACH, SHAN])
    ask = eng.pending
    assert ask.data['zhangba'] and len(ask.data['cards']) == 1
    eng.apply(PlayCards('b', (cid(eng, 'b', SHA),)))         # 出真杀
    assert eng.player('c').hp == 3
    assert eng.player('b').weapon is not None

    eng = _borrow_zhangba_setup([SHA, SHAN, PEACH, SHAN])
    c1, c2 = (c.cid for c in eng.player('b').hand[1:3])      # 两牌当杀
    eng.apply(PlayCards('b', (c1, c2)))
    assert eng.player('c').hp == 3
    assert eng.player('b').weapon is not None


def test_borrow_sword_zhangba_rejects_bad_cids():
    """单张非杀、同一张牌计两次、无丈八蛇矛出两牌，均为非法动作。"""
    eng = _borrow_zhangba_setup([SHAN, SHAN, PEACH, SHAN])
    b = eng.player('b')
    with pytest.raises(IllegalAction):
        eng.apply(PlayCards('b', (b.hand[0].cid,)))          # 单张非杀
    with pytest.raises(IllegalAction):
        eng.apply(PlayCards('b', (b.hand[0].cid, b.hand[0].cid)))

    eng = _borrow_setup()       # b 装的是青釭剑，手牌有杀
    play_card(eng, 'a', BORROW, 'b')
    eng.apply(PlayCards('a', (), 'c'))
    b = eng.player('b')
    with pytest.raises(IllegalAction):
        eng.apply(PlayCards('b', (b.hand[0].cid, b.hand[1].cid)))


# ---------- 装备区拆顺 / 死亡清理 ----------

def test_dismantle_equipment():
    hands = sha_hands()
    hands[0] = [CARD_NAME['dismantle'], SHA, SHA, SHA]
    eng = start_engine(hands)
    eng.player('c').weapon = equip(901, GUANSHI, '3')
    play_card(eng, 'a', CARD_NAME['dismantle'], 'c')
    options = eng.pending.data['cards']
    weapon_opt = [opt for opt in options if opt[1] and GUANSHI in opt[1]]
    assert weapon_opt
    eng.apply(PlayCards('a', (weapon_opt[0][0],)))
    assert eng.player('c').weapon is None
    assert any(c.cid == 901 for c in eng.discard_pile)


def test_death_discards_equipment():
    eng = start_engine(sha_hands())
    b = eng.player('b')
    b.hp = 1
    b.weapon = equip(901, QINGGANG, '2')
    b.plus_horse = equip(902, '绝影', '+1')
    play_sha(eng, 'a', 'b')
    assert not b.alive
    assert b.weapon is None and b.plus_horse is None
    assert any(c.cid == 901 for c in eng.discard_pile)
    assert any(c.cid == 902 for c in eng.discard_pile)

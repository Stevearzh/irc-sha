"""锦囊牌测试：无懈可击（含嵌套）、决斗、南蛮/万箭、顺手/过河、
无中/五谷/桃园、乐不思蜀/闪电（延时锦囊与判定阶段）。"""

import random

import pytest

from isha.core.actions import Pass, PlayCards
from isha.core.cards import make_card
from isha.core.deck import build_deck
from isha.core.engine import IllegalAction
from isha.dict.card import CARD_NAME

from helpers import (H, PEACH, SHA, SHAN, cid, kinds, pass_play_and_discard,
                     play_card, play_sha, sha_hands, start_engine)

NEGATE = CARD_NAME['negate']
DUEL = CARD_NAME['duel']
SAVAGE = CARD_NAME['savage']
ARROWS = CARD_NAME['arrows']
SNATCH = CARD_NAME['snatch']
DISMANTLE = CARD_NAME['dismantle']
EXNIHILO = CARD_NAME['exnihilo']
HARVEST = CARD_NAME['harvest']
GARDEN = CARD_NAME['garden']
CONTENTMENT = CARD_NAME['contentment']
LIGHTNING = CARD_NAME['lightning']


# ---------- 无懈可击 ----------

def test_duel_negated():
    hands = sha_hands()
    hands[0] = [DUEL, SHA, SHA, SHA]
    hands[1] = [SHAN] * 4                 # b 无杀无懈
    hands[2] = [NEGATE, SHA, SHA, SHA]    # c 有无懈可击
    eng = start_engine(hands)
    play_card(eng, 'a', DUEL, 'b')
    assert eng.pending.kind == 'negate' and eng.pending.player == 'c'
    effects = eng.apply(PlayCards('c', (cid(eng, 'c', NEGATE),)))
    assert 'negate_used' in kinds(effects) and 'negated' in kinds(effects)
    assert eng.player('b').hp == 4        # 决斗被抵消，无伤害
    assert eng.pending.kind == 'play' and eng.pending.player == 'a'


def test_duel_double_negate_proceeds():
    hands = sha_hands()
    hands[0] = [DUEL, NEGATE, SHA, SHA]   # a 有无懈可击可反制
    hands[1] = [SHAN] * 4                 # b 无杀
    hands[2] = [NEGATE, SHA, SHA, SHA]
    eng = start_engine(hands)
    play_card(eng, 'a', DUEL, 'b')
    assert eng.pending.player == 'a'      # 窗口从出锦囊者开始询问
    effects = eng.apply(Pass('a'))        # a 不抵消自己的决斗
    effects += eng.apply(PlayCards('c', (cid(eng, 'c', NEGATE),)))   # c 抵消（1 层）
    assert eng.pending.player == 'a'      # 重新一轮：a 反制（2 层）
    effects += eng.apply(PlayCards('a', (cid(eng, 'a', NEGATE),)))
    assert kinds(effects).count('negate_used') == 2
    assert eng.player('b').hp == 3        # 偶数层抵消无效，决斗生效：b 无杀受伤


def test_negate_chain_triple():
    """无懈可击抵消无懈可击再被抵消：3 层（奇数）→ 原锦囊被抵消。"""
    hands = sha_hands()
    hands[0] = [DUEL, NEGATE, SHA, SHA]       # a 有 1 张无懈
    hands[1] = [SHAN] * 4                     # b 无杀
    hands[2] = [NEGATE, NEGATE, SHA, SHA]     # c 有 2 张无懈
    eng = start_engine(hands)
    play_card(eng, 'a', DUEL, 'b')
    eng.apply(Pass('a'))                      # a 不抵消自己的决斗
    eng.apply(PlayCards('c', (cid(eng, 'c', NEGATE, 0),)))   # 1 层：c 抵消
    eng.apply(PlayCards('a', (cid(eng, 'a', NEGATE),)))      # 2 层：a 反制
    assert eng.pending.kind == 'negate' and eng.pending.player == 'c'
    effects = eng.apply(PlayCards('c', (cid(eng, 'c', NEGATE),)))  # 3 层：c 再抵消
    assert 'negated' in kinds(effects)
    assert eng.player('b').hp == 4            # 奇数层：决斗被抵消，无伤害


def test_negate_not_playable_actively():
    hands = sha_hands()
    hands[0] = [NEGATE, SHA, SHA, SHA]
    eng = start_engine(hands)
    with pytest.raises(IllegalAction):
        eng.apply(PlayCards('a', (cid(eng, 'a', NEGATE),)))


def test_savage_per_target_negate():
    hands = sha_hands()
    hands[0] = [SAVAGE, SHA, SHA, SHA]
    hands[1] = [SHAN] * 4                 # b 无杀：本应受伤
    hands[2] = [NEGATE, SHA, SHA, SHA]    # c 有无懈可击
    hands[3] = [SHAN] * 4
    hands[4] = [SHAN] * 4
    eng = start_engine(hands)
    play_card(eng, 'a', SAVAGE)
    assert eng.pending.kind == 'negate' and eng.pending.player == 'c'
    effects = eng.apply(PlayCards('c', (cid(eng, 'c', NEGATE),)))
    assert 'negated' in kinds(effects)    # 仅抵消南蛮对 b 的效果
    # c 自己仍需响应：有杀，打出
    assert eng.pending.kind == 'respond_aoe' and eng.pending.player == 'c'
    eng.apply(PlayCards('c', (cid(eng, 'c', SHA),)))
    assert eng.player('b').hp == 4
    assert eng.player('c').hp == 4
    assert eng.player('d').hp == 3 and eng.player('e').hp == 3


def test_negate_window_hints_response_cards():
    """无懈可击窗口：目标本人被询问时提示其手上的响应牌（决斗→杀）。"""
    hands = sha_hands()
    hands[0] = [DUEL, SHA, SHA, SHA]
    hands[1] = [NEGATE, SHA, SHA, SHAN]      # b 是目标：1 张无懈 + 2 张杀
    hands[2] = [NEGATE, SHAN, SHAN, SHAN]    # c 是第三方：有无懈
    eng = start_engine(hands)
    play_card(eng, 'a', DUEL, 'b')
    assert eng.pending.kind == 'negate' and eng.pending.player == 'b'
    d = eng.pending.data
    assert d['response_name'] == SHA
    assert [lab for _, lab in d['response_cards']] == ['♠A杀', '♠A杀']
    eng.apply(Pass('b'))
    # 第三方被询问：不附带目标的响应牌信息（手牌保密）
    assert eng.pending.kind == 'negate' and eng.pending.player == 'c'
    assert 'response_name' not in eng.pending.data


def test_negate_window_hints_shan_for_arrows():
    """万箭齐发的无懈窗口：提示目标手上的闪。"""
    hands = sha_hands()
    hands[0] = [ARROWS, SHA, SHA, SHA]
    hands[1] = [NEGATE, SHAN, SHAN, SHAN]    # b 有 1 张无懈 + 3 张闪
    eng = start_engine(hands)
    play_card(eng, 'a', ARROWS)
    assert eng.pending.kind == 'negate' and eng.pending.player == 'b'
    d = eng.pending.data
    assert d['response_name'] == SHAN
    assert len(d['response_cards']) == 3


def test_negate_window_no_hint_for_plain_trick():
    """无响应牌的锦囊（顺手牵羊）：无懈窗口不附带响应提示。"""
    hands = sha_hands()
    hands[0] = [SNATCH, SHA, SHA, SHA]
    hands[1] = [NEGATE, SHA, SHA, SHA]
    eng = start_engine(hands)
    play_card(eng, 'a', SNATCH, 'b')
    assert eng.pending.kind == 'negate' and eng.pending.player == 'b'
    assert 'response_name' not in eng.pending.data


def test_negate_rest_skips_later_windows():
    """Pass(rest=True)：本张锦囊后续目标的无懈窗口不再询问该玩家。"""
    hands = sha_hands()
    hands[0] = [SAVAGE, SHA, SHA, SHA]
    hands[1] = [NEGATE, SHA, SHA, SHA]    # b 有无懈，rest
    hands[3] = [NEGATE, SHA, SHA, SHA]    # d 有无懈，普通 pass
    eng = start_engine(hands)
    play_card(eng, 'a', SAVAGE)
    # 目标 b 的无懈窗口：b rest，d 普通 pass
    assert eng.pending.kind == 'negate' and eng.pending.player == 'b'
    eng.apply(Pass('b', rest=True))
    assert eng.pending.kind == 'negate' and eng.pending.player == 'd'
    eng.apply(Pass('d'))
    # b 响应自己的南蛮
    assert eng.pending.kind == 'respond_aoe' and eng.pending.player == 'b'
    eng.apply(PlayCards('b', (cid(eng, 'b', SHA),)))
    # 目标 c 的无懈窗口：b 已被跳过，直接问 d
    assert eng.pending.kind == 'negate' and eng.pending.player == 'd'
    eng.apply(Pass('d'))
    assert eng.pending.kind == 'respond_aoe' and eng.pending.player == 'c'


def test_negate_rest_reset_on_counter():
    """rest 后若有人打出无懈可击，新一轮询问中该玩家会重新被问。"""
    hands = sha_hands()
    hands[0] = [SAVAGE, SHA, SHA, SHA]
    hands[1] = [NEGATE, NEGATE, SHA, SHA]   # b 有两张无懈：先 rest，后反制
    hands[2] = [NEGATE, SHA, SHA, SHA]      # c 打出无懈
    eng = start_engine(hands)
    play_card(eng, 'a', SAVAGE)
    assert eng.pending.kind == 'negate' and eng.pending.player == 'b'
    eng.apply(Pass('b', rest=True))
    assert eng.pending.kind == 'negate' and eng.pending.player == 'c'
    eng.apply(PlayCards('c', (cid(eng, 'c', NEGATE),)))   # c 抵消 → 新一轮
    assert eng.pending.kind == 'negate' and eng.pending.player == 'b'
    eng.apply(PlayCards('b', (cid(eng, 'b', NEGATE),)))  # b 反制 → 又一轮
    assert eng.pending.kind == 'negate' and eng.pending.player == 'b'


# ---------- 决斗 / AOE ----------

def test_duel_exchange():
    hands = sha_hands()
    hands[0] = [DUEL, SHA, SHA, SHA]      # a 有杀可回
    hands[1] = [SHA] * 4                  # b 有杀
    eng = start_engine(hands)
    play_card(eng, 'a', DUEL, 'b')
    assert eng.pending.kind == 'duel' and eng.pending.player == 'b'
    eng.apply(PlayCards('b', (cid(eng, 'b', SHA),)))   # b 回杀
    assert eng.pending.kind == 'duel' and eng.pending.player == 'a'
    effects = eng.apply(Pass('a'))                      # a 不出杀
    assert 'damaged' in kinds(effects)
    assert eng.player('a').hp == 4        # 主公 5 血 → 4


def test_savage_assault():
    hands = sha_hands()
    hands[0] = [SAVAGE, SHA, SHA, SHA]
    hands[2] = [SHAN] * 4                 # c 无杀
    hands[3] = [SHA] * 4                  # d 有杀但选择不出
    hands[4] = [SHAN] * 4                 # e 无杀
    eng = start_engine(hands)
    play_card(eng, 'a', SAVAGE)
    eng.apply(PlayCards('b', (cid(eng, 'b', SHA),)))   # b 出杀响应
    eng.apply(Pass('d'))                                # d 不出杀
    assert eng.player('b').hp == 4
    assert eng.player('c').hp == 3
    assert eng.player('d').hp == 3
    assert eng.player('e').hp == 3


def test_arrow_barrage():
    hands = sha_hands()
    hands[0] = [ARROWS, SHA, SHA, SHA]
    hands[1] = [SHAN] * 4                 # b 有闪
    eng = start_engine(hands)
    play_card(eng, 'a', ARROWS)
    eng.apply(PlayCards('b', (cid(eng, 'b', SHAN),)))
    assert eng.player('b').hp == 4
    assert all(eng.player(n).hp == 3 for n in ('c', 'd', 'e'))


# ---------- 顺手 / 过河 ----------

def test_snatch():
    hands = sha_hands()
    hands[0] = [SNATCH, SNATCH, SHA, SHA]
    eng = start_engine(hands)
    play_card(eng, 'a', SNATCH, 'b')
    # 选择窗口：目标手牌为暗牌（label 为 None，按位置盲选）
    assert eng.pending.kind == 'choose_card' and eng.pending.player == 'a'
    options = eng.pending.data['cards']
    assert all(label is None for _, label in options)
    eng.apply(PlayCards('a', (options[0][0],)))
    assert len(eng.player('b').hand) == 3
    assert len(eng.king.hand) == 6        # 6 - 1(打出) + 1(牵来)
    with pytest.raises(IllegalAction):
        play_card(eng, 'a', SNATCH, 'c')  # c 距离 2，牵不到


def test_dismantle():
    hands = sha_hands()
    hands[0] = [DISMANTLE, SHA, SHA, SHA]
    eng = start_engine(hands)
    play_card(eng, 'a', DISMANTLE, 'c')   # 过河拆桥不限距离
    assert eng.pending.kind == 'choose_card'
    options = eng.pending.data['cards']
    effects = eng.apply(PlayCards('a', (options[1][0],)))
    assert 'dismantle' in kinds(effects)
    assert len(eng.player('c').hand) == 3
    # 弃置的牌公开
    assert effects[kinds(effects).index('dismantle')].data['label']


def test_raid_judgement_area():
    """顺手/过河可以选择判定区的明牌（如拆乐不思蜀）。"""
    hands = sha_hands()
    hands[0] = [CONTENTMENT, DISMANTLE, SHA, SHA]
    eng = start_engine(hands)
    play_card(eng, 'a', CONTENTMENT, 'b')         # 乐不思蜀置入 b 判定区
    eng.player('b').hand = []                     # 白盒：b 手牌清空
    play_card(eng, 'a', DISMANTLE, 'b')           # b 无手牌但有判定区，仍可指定
    options = eng.pending.data['cards']
    assert options == [(eng.pending.data['cards'][0][0], '♠A乐不思蜀')]
    effects = eng.apply(PlayCards('a', (options[0][0],)))
    assert eng.player('b').judgement == []
    assert 'dismantle' in kinds(effects)


def test_snatch_judgement_area():
    hands = sha_hands()
    hands[0] = [CONTENTMENT, SNATCH, SHA, SHA]
    eng = start_engine(hands)
    play_card(eng, 'a', CONTENTMENT, 'b')
    play_card(eng, 'a', SNATCH, 'b')
    options = eng.pending.data['cards']
    cid_j, label_j = options[-1]                  # 判定区明牌排在手牌后
    assert label_j == '♠A乐不思蜀'
    eng.apply(PlayCards('a', (cid_j,)))
    assert eng.player('b').judgement == []
    assert '♠A乐不思蜀' in [c.label for c in eng.king.hand]


def test_choose_card_rejects_bad_cid():
    hands = sha_hands()
    hands[0] = [DISMANTLE, SHA, SHA, SHA]
    eng = start_engine(hands)
    play_card(eng, 'a', DISMANTLE, 'c')
    with pytest.raises(IllegalAction):
        eng.apply(PlayCards('a', (9999,)))


def test_choose_card_timeout_picks_first():
    hands = sha_hands()
    hands[0] = [DISMANTLE, SHA, SHA, SHA]
    eng = start_engine(hands)
    play_card(eng, 'a', DISMANTLE, 'c')
    eng.timeout()
    assert len(eng.player('c').hand) == 3


# ---------- 增益锦囊 ----------

def test_ex_nihilo():
    hands = sha_hands()
    hands[0] = [EXNIHILO, SHA, SHA, SHA]
    eng = start_engine(hands)
    play_card(eng, 'a', EXNIHILO)
    assert len(eng.king.hand) == 6 - 1 + 2


def test_garden():
    hands = sha_hands()
    hands[0] = [GARDEN, SHA, SHA, SHA]
    eng = start_engine(hands)
    eng.player('b').hp = 2
    eng.player('c').hp = 1
    eng.pending = eng._play_ask(eng.king)   # 白盒：掉血后重建询问
    effects = play_card(eng, 'a', GARDEN)
    assert eng.player('b').hp == 3 and eng.player('c').hp == 2
    assert eng.king.hp == 5                 # 满血不受影响
    assert kinds(effects).count('healed') == 2


def test_harvest():
    hands = sha_hands()
    hands[0] = [HARVEST, SHA, SHA, SHA]
    rest = [PEACH, SHAN, DUEL, SHA] * 10   # 亮出的牌不含无懈可击，避免插入抵消窗口
    eng = start_engine(hands, rest=rest)
    play_card(eng, 'a', HARVEST)
    # 亮出 5 张（主公已先摸走 rest 前 2 张）
    for nick in ('a', 'b', 'c', 'd', 'e'):
        assert eng.pending.kind == 'harvest' and eng.pending.player == nick
        first = eng.pending.data['revealed'][0][0]
        eng.apply(PlayCards(nick, (first,)))
    assert all(len(p.hand) >= 4 for p in eng.players)
    assert len(eng.king.hand) == 6 - 1 + 1


def test_harvest_timeout_picks_first():
    hands = sha_hands()
    hands[0] = [HARVEST, SHA, SHA, SHA]
    rest = [PEACH, SHAN, DUEL, SHA] * 10
    eng = start_engine(hands, rest=rest)
    play_card(eng, 'a', HARVEST)
    first_label = eng.pending.data['revealed'][0][1]
    eng.timeout()
    assert first_label in [c.label for c in eng.king.hand]


# ---------- 延时锦囊与判定阶段 ----------

def test_delayed_no_negate_window_at_placement():
    """延时锦囊使用时置入判定区、不结算：此时不开无懈可击窗口。"""
    hands = sha_hands()
    hands[0] = [LIGHTNING, SHA, SHA, SHA]
    hands[1] = [NEGATE, SHA, SHA, SHA]
    eng = start_engine(hands)
    effects = play_card(eng, 'a', LIGHTNING)
    assert 'trick_placed' in kinds(effects)
    assert 'negate_used' not in kinds(effects)
    # 直接回到出牌阶段，没有任何抵消询问
    assert eng.pending.kind == 'play' and eng.pending.player == 'a'


def test_contentment_negated_at_judgement():
    """乐不思蜀的无懈可击时机：判定阶段、翻判定牌之前。"""
    hands = sha_hands()
    hands[0] = [CONTENTMENT, SHA, SHA, SHA]
    hands[1] = [NEGATE, SHA, SHA, SHA]    # b 持有无懈可击
    eng = start_engine(hands)
    play_card(eng, 'a', CONTENTMENT, 'b')
    eng.apply(Pass('a'))                  # a 结束 → b 的判定阶段开窗
    assert eng.pending.kind == 'negate' and eng.pending.player == 'b'
    effects = eng.apply(PlayCards('b', (cid(eng, 'b', NEGATE),)))
    assert 'negated' in kinds(effects)
    assert 'judge_flip' not in kinds(effects)   # 被抵消则不翻判定牌
    assert 'skip_play' not in kinds(effects)
    assert eng.player('b').judgement == []      # 乐不思蜀被弃置
    assert eng.pending.kind == 'play' and eng.pending.player == 'b'


def test_lightning_negated_at_judgement():
    """闪电在判定前被无懈可击抵消：不判定、直接移至下家判定区（官方裁定）。"""
    hands = sha_hands()
    hands[0] = [LIGHTNING, SHA, SHA, SHA]
    hands[1] = [SHA, SHA, SHA, NEGATE]    # 弃牌默认弃前面的，保住无懈可击
    eng = start_engine(hands)
    play_card(eng, 'a', LIGHTNING)
    pass_play_and_discard(eng)              # a
    for _ in range(4):
        pass_play_and_discard(eng)          # b c d e → a 的第二回合判定
    assert eng.pending.kind == 'negate' and eng.pending.player == 'b'
    effects = eng.apply(PlayCards('b', (cid(eng, 'b', NEGATE),)))
    assert 'negated' in kinds(effects) and 'lightning_move' in kinds(effects)
    assert 'judge_flip' not in kinds(effects)
    assert eng.king.hp == 5
    assert eng.king.judgement == []
    # 闪电移至下家 b 的判定区而非弃置
    assert [c.name for c in eng.player('b').judgement] == [LIGHTNING]


def test_dying_needs_three_peaches_from_negative_hp():
    """1 血被闪电命中（3 点伤害）→ hp 为 -2 → 需要 3 个桃才能救回。"""
    hands = sha_hands()
    hands[2] = [PEACH, PEACH, PEACH, SHA]         # c 有 3 个桃
    eng = start_engine(hands)
    b = eng.player('b')
    b.hp = 1
    b.judgement.append(make_card(999, '♠', '2', LIGHTNING))   # 白盒：b 挂着闪电
    eng.deck[0] = make_card(998, '♠', '5', SHA)   # b 的判定牌：黑桃5 → 命中
    effects = pass_play_and_discard(eng)          # a 结束 → b 判定
    assert effects[kinds(effects).index('damaged')].data['hp'] == -2
    for i in range(3):                            # c 连续出 3 个桃
        assert eng.pending.kind == 'peach' and eng.pending.player == 'c'
        effects = eng.apply(PlayCards('c', (cid(eng, 'c', PEACH),)))
    assert kinds(effects).count('peach_used') == 1
    assert b.alive and b.hp == 1                  # -2 + 3 = 1，脱离濒死
    assert eng.pending.kind == 'play' and eng.pending.player == 'b'


def test_dying_not_enough_peaches_dies():
    """桃不够（-2 只补到 0）→ 仍然死亡。"""
    hands = sha_hands()
    hands[2] = [PEACH, PEACH, SHA, SHA]           # c 只有 2 个桃
    eng = start_engine(hands)
    b = eng.player('b')
    b.hp = 1
    b.judgement.append(make_card(999, '♠', '2', LIGHTNING))
    eng.deck[0] = make_card(998, '♠', '5', SHA)
    pass_play_and_discard(eng)                    # a 结束 → b 判定
    eng.apply(PlayCards('c', (cid(eng, 'c', PEACH),)))   # -2 → -1
    effects = eng.apply(PlayCards('c', (cid(eng, 'c', PEACH),)))   # -1 → 0
    assert 'died' in kinds(effects)
    assert not b.alive and b.hp == 0


def test_death_discards_judgement_area():
    """玩家死亡：手牌与判定区的牌全部置入弃牌堆。"""
    hands = sha_hands()
    eng = start_engine(hands)
    b = eng.player('b')
    b.hp = 1
    b.judgement.append(make_card(999, H, '3', CONTENTMENT))
    play_sha(eng, 'a', 'b')                   # b 无闪直接濒死，无人有桃
    assert not b.alive
    assert b.judgement == [] and b.hand == []
    assert any(c.cid == 999 for c in eng.discard_pile)


def test_death_mid_judge_discards_remaining():
    """判定中途死亡（闪电先判并命中）：剩余的乐不思蜀不再判定，直接弃置。"""
    hands = sha_hands()
    eng = start_engine(hands)
    b = eng.player('b')
    b.hp = 1
    b.judgement.append(make_card(990, H, '3', CONTENTMENT))   # 先挂乐不思蜀
    b.judgement.append(make_card(999, '♠', '2', LIGHTNING))   # 后挂闪电，先判
    eng.deck[0] = make_card(998, '♠', '5', SHA)   # 闪电判定牌：黑桃5 → 命中
    effects = pass_play_and_discard(eng)          # a 结束 → b 判定
    flips = [e for e in effects if e.kind == 'judge_flip']
    assert len(flips) == 1 and flips[0].data['reason'] == LIGHTNING
    assert 'died' in kinds(effects)
    assert b.judgement == []
    assert any(c.cid == 990 for c in eng.discard_pile)   # 乐不思蜀未判定直接弃置
    assert any(c.cid == 999 for c in eng.discard_pile)


def test_lightning_skips_player_with_lightning():
    """闪电移动时跳过判定区已有闪电的玩家。"""
    hands = sha_hands()
    hands[0] = [LIGHTNING, SHA, SHA, SHA]
    eng = start_engine(hands)
    eng.deck[8] = make_card(998, H, '7', SHA)     # a 第二回合判定：不中
    play_card(eng, 'a', LIGHTNING)
    b = eng.player('b')
    b.judgement.append(make_card(999, '♥', 'Q', LIGHTNING))   # b 已有闪电
    pass_play_and_discard(eng)                    # a
    for _ in range(4):
        pass_play_and_discard(eng)                # b c d e → a 判定
    assert [c.name for c in b.judgement] == [LIGHTNING]       # b 自己的还在
    assert [c.name for c in eng.player('c').judgement] == [LIGHTNING]  # 传给 c


def test_cannot_stack_lightning():
    """判定区已有闪电的玩家不能再挂闪电。"""
    hands = sha_hands()
    hands[0] = [LIGHTNING, SHA, SHA, SHA]
    eng = start_engine(hands)
    eng.king.judgement.append(make_card(999, '♠', 'A', LIGHTNING))
    eng.pending = eng._play_ask(eng.king)   # 白盒：选项固化，重建询问
    with pytest.raises(IllegalAction):
        play_card(eng, 'a', LIGHTNING)


def test_cannot_stack_contentment():
    """判定区已有乐不思蜀的角色不能再成为乐不思蜀的目标。"""
    hands = sha_hands()
    hands[0] = [CONTENTMENT, SHA, SHA, SHA]
    eng = start_engine(hands)
    eng.player('b').judgement.append(make_card(999, '♠', '6', CONTENTMENT))
    eng.pending = eng._play_ask(eng.king)
    with pytest.raises(IllegalAction):
        play_card(eng, 'a', CONTENTMENT, 'b')
    play_card(eng, 'a', CONTENTMENT, 'c')         # 其他玩家仍可指定
    assert [c.name for c in eng.player('c').judgement] == [CONTENTMENT]


def test_judgement_lifo_order():
    """判定区多张延时锦囊：后到先判（先判乐不思蜀，后判闪电）。"""
    hands = sha_hands()
    hands[0] = [LIGHTNING, SHA, SHA, SHA]       # a 先给自己挂闪电
    hands[2] = [CONTENTMENT, SHA, SHA, SHA]     # c 随后给 a 挂乐不思蜀
    eng = start_engine(hands)
    # a 第二回合的两张判定牌（b/c/d/e 各摸 2 张后，牌堆顶第 9、10 张）
    eng.deck[8] = make_card(998, H, '7', SHA)   # 乐不思蜀：红桃 → 不跳过出牌
    eng.deck[9] = make_card(997, '♠', '5', SHA)  # 闪电：黑桃5 → 命中
    play_card(eng, 'a', LIGHTNING)
    pass_play_and_discard(eng)                  # a
    pass_play_and_discard(eng)                  # b
    play_card(eng, 'c', CONTENTMENT, 'a')       # c 给 a 挂乐不思蜀
    pass_play_and_discard(eng)                  # c
    pass_play_and_discard(eng)                  # d
    effects = pass_play_and_discard(eng)        # e → a 的第二回合判定
    flips = [e.data['reason'] for e in effects if e.kind == 'judge_flip']
    assert flips == [CONTENTMENT, LIGHTNING]    # 后到先判
    assert 'skip_play' not in kinds(effects)    # 红桃，不跳过出牌
    assert eng.king.hp == 5 - 3                 # 闪电命中
    assert eng.king.judgement == []             # 两张都已结算


def test_contentment_skips_play():
    hands = sha_hands()
    hands[0] = [CONTENTMENT, SHA, SHA, SHA]
    eng = start_engine(hands)
    play_card(eng, 'a', CONTENTMENT, 'b')   # 判定牌默认黑桃 → 跳过出牌
    assert len(eng.player('b').judgement) == 1
    effects = pass_play_and_discard(eng)    # a 结束 → b 的回合判定
    assert 'judge_flip' in kinds(effects) and 'skip_play' in kinds(effects)
    assert eng.pending.kind == 'discard' and eng.pending.player == 'b'
    assert eng.player('b').judgement == []  # 判定后弃置


def test_contentment_heart_no_skip():
    hands = sha_hands()
    hands[0] = [CONTENTMENT, SHA, SHA, SHA]
    eng = start_engine(hands)
    play_card(eng, 'a', CONTENTMENT, 'b')
    eng.deck[0] = make_card(999, H, '5', SHA)   # 白盒：判定牌换红桃
    effects = pass_play_and_discard(eng)
    assert 'judge_flip' in kinds(effects)
    assert 'skip_play' not in kinds(effects)
    assert eng.pending.kind == 'play' and eng.pending.player == 'b'


def _drive_until_kings_second_turn(eng):
    play_card(eng, 'a', LIGHTNING)
    pass_play_and_discard(eng)              # a
    for _ in range(4):
        pass_play_and_discard(eng)          # b c d e
    # a 的第二回合：判定在上一轮 e 结束时的 apply 中已发生


def test_lightning_strikes():
    hands = sha_hands()
    hands[0] = [LIGHTNING, SHA, SHA, SHA]
    eng = start_engine(hands)
    eng.deck[8] = make_card(998, '♠', '5', SHA)   # a 第二回合的判定牌：黑桃5
    _drive_until_kings_second_turn(eng)
    assert eng.king.hp == 5 - 3
    assert eng.king.judgement == []
    assert eng.player('b').judgement == []


def test_lightning_moves_on():
    hands = sha_hands()
    hands[0] = [LIGHTNING, SHA, SHA, SHA]
    eng = start_engine(hands)
    eng.deck[8] = make_card(998, H, '7', SHA)     # 红桃：不中，移给下家
    _drive_until_kings_second_turn(eng)
    assert eng.king.hp == 5
    assert eng.king.judgement == []
    assert [c.name for c in eng.player('b').judgement] == [LIGHTNING]


# ---------- 牌堆构成 ----------

def test_full_deck_composition():
    from isha.card import DEFAULT_CARD_TYPES, DEFAULT_RULES
    deck = build_deck('package/card/', ['common'], set(DEFAULT_RULES),
                      random.Random(1), DEFAULT_CARD_TYPES)
    assert len(deck) == 104   # 完整标准包：基本牌 + 锦囊 + 装备


def test_ex_deck_composition():
    """EX 卡包：标准包 104 张 + EX 4 张（寒冰剑、闪电、仁王盾、无懈可击）。"""
    from isha.card import DEFAULT_CARD_TYPES, DEFAULT_RULES
    deck = build_deck('package/card/', ['common', 'ex'], set(DEFAULT_RULES),
                      random.Random(1), DEFAULT_CARD_TYPES)
    assert len(deck) == 108


# ---------- 判定区可见性 ----------

def test_judgement_visible_in_table_and_web_state():
    import json
    from isha.game.render import render_table
    from isha.game.web import Game

    hands = sha_hands()
    hands[0] = [CONTENTMENT, SHA, SHA, SHA]
    eng = start_engine(hands)
    play_card(eng, 'a', CONTENTMENT, 'b')

    assert '♠A乐不思蜀' in render_table(eng)          # CLI 局势面板可见

    g = Game.__new__(Game)                            # Web 状态对所有玩家可见
    g.engine, g.log, g.deadline = eng, [], None
    s = g.state()
    json.dumps(s, ensure_ascii=False)
    assert s['players'][1]['judgement'] == ['♠A乐不思蜀']

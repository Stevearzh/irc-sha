import pytest

from isha.core.actions import DiscardCards, Pass, PlayCards
from isha.core.engine import IllegalAction
from isha.dict.identity import IDENTITY
from isha.game import new_game

from helpers import (PEACH, SHA, SHAN, cid, kinds, pass_play_and_discard,
                     play_sha, sha_hands, start_engine)


# ---------- 开局 ----------

def test_game_start():
    eng = start_engine(sha_hands())
    assert eng.king.nick == 'a'
    assert eng.king.max_hp == 5 and eng.king.hp == 5
    assert len(eng.king.hand) == 6   # 4 + 摸牌阶段 2
    assert all(len(p.hand) == 4 for p in eng.players[1:])
    assert eng.pending.kind == 'play' and eng.pending.player == 'a'
    assert eng.turn_no == 1 and eng.phase == 'play'


def test_new_game_deterministic():
    nicks = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    g1 = new_game(nicks, seed=7)
    g2 = new_game(nicks, seed=7)
    assert [p.nick for p in g1.players] == [p.nick for p in g2.players]
    assert [p.identity for p in g1.players] == [p.identity for p in g2.players]
    assert [[c.label for c in p.hand] for p in g1.players] == \
           [[c.label for c in p.hand] for p in g2.players]


# ---------- 杀 / 闪 ----------

def test_sha_dodge():
    hands = sha_hands()
    hands[1] = [SHAN, SHA, SHA, SHA]
    eng = start_engine(hands)
    effects = play_sha(eng, 'a', 'b')
    assert 'card_used' in kinds(effects)
    assert eng.pending.kind == 'respond_sha' and eng.pending.player == 'b'
    effects = eng.apply(PlayCards('b', (cid(eng, 'b', SHAN),)))
    assert 'dodge' in kinds(effects)
    assert eng.player('b').hp == 4


def test_sha_hit_damage():
    hands = sha_hands()
    hands[1] = [SHAN, SHA, SHA, SHA]
    eng = start_engine(hands)
    play_sha(eng, 'a', 'b')
    assert eng.pending.kind == 'respond_sha'
    effects = eng.apply(Pass('b'))
    assert 'damaged' in kinds(effects)
    assert eng.player('b').hp == 3
    assert eng.pending.kind == 'play' and eng.pending.player == 'a'


def test_sha_without_shan_hits_directly():
    eng = start_engine(sha_hands())
    effects = play_sha(eng, 'a', 'b')
    assert 'damaged' in kinds(effects)   # b 没有闪，不经询问直接受伤
    assert eng.player('b').hp == 3


def test_one_sha_per_turn():
    eng = start_engine(sha_hands())
    play_sha(eng, 'a', 'b')            # b 无闪直接受伤
    with pytest.raises(IllegalAction):
        play_sha(eng, 'a', 'b', i=0)   # 本回合已出过杀


def test_sha_distance_limit():
    eng = start_engine(sha_hands())
    with pytest.raises(IllegalAction):
        play_sha(eng, 'a', 'c')        # a-c 距离为 2，超出攻击范围 1


def test_dead_players_shrink_distance():
    hands = sha_hands()
    hands[1] = [SHAN, SHA, SHA, SHA]
    eng = start_engine(hands)
    eng.player('b').hp = 1
    play_sha(eng, 'a', 'b')
    eng.apply(Pass('b'))               # b 阵亡
    assert eng.distance('a', 'c') == 1   # b 离场后 a-c 距离收缩为 1


# ---------- 桃 ----------

def test_peach_heal():
    hands = sha_hands()
    hands[0] = [PEACH, SHA, SHA, SHA]
    eng = start_engine(hands)
    eng.king.hp = 3
    eng.pending = eng._play_ask(eng.king)   # 白盒：选项在挂起时固化，掉血后重建询问
    effects = eng.apply(PlayCards('a', (cid(eng, 'a', PEACH),)))
    assert 'healed' in kinds(effects)
    assert eng.king.hp == 4


def test_peach_not_playable_at_full_hp():
    hands = sha_hands()
    hands[0] = [PEACH, SHA, SHA, SHA]
    eng = start_engine(hands)
    with pytest.raises(IllegalAction):
        eng.apply(PlayCards('a', (cid(eng, 'a', PEACH),)))


# ---------- 弃牌 ----------

def test_discard_down_to_hp():
    eng = start_engine(sha_hands())
    eng.apply(Pass('a'))               # 手牌 6 > hp 5
    assert eng.pending.kind == 'discard'
    assert eng.pending.data['count'] == 1
    effects = eng.apply(DiscardCards('a', (eng.king.hand[0].cid,)))
    assert 'discard' in kinds(effects) and 'turn_end' in kinds(effects)
    assert eng.pending.player == 'b' and eng.turn_no == 2


def test_discard_rejects_wrong_count():
    eng = start_engine(sha_hands())
    eng.apply(Pass('a'))
    with pytest.raises(IllegalAction):
        eng.apply(DiscardCards('a', tuple()))


# ---------- 濒死 / 死亡 / 胜负 ----------

def test_dying_saved_by_peach():
    hands = sha_hands()
    hands[1] = [SHAN, SHA, SHA, SHA]
    hands[2] = [PEACH, SHA, SHA, SHA]
    eng = start_engine(hands)
    eng.player('b').hp = 1
    play_sha(eng, 'a', 'b')
    eng.apply(Pass('b'))               # b 有闪但选择不出，进入濒死
    assert eng.pending.kind == 'peach' and eng.pending.player == 'c'
    effects = eng.apply(PlayCards('c', (cid(eng, 'c', PEACH),)))
    assert 'peach_used' in kinds(effects)
    assert eng.player('b').alive and eng.player('b').hp == 1


def test_death_rebel_reward():
    hands = sha_hands()
    hands[1] = [SHAN, SHA, SHA, SHA]
    eng = start_engine(hands)
    eng.player('b').hp = 1
    play_sha(eng, 'a', 'b')
    effects = eng.apply(Pass('b'))
    assert 'died' in kinds(effects)
    assert not eng.player('b').alive
    assert eng.player('b').hand == []
    assert 'reward' in kinds(effects)   # 击杀反贼摸 3 张
    assert len(eng.king.hand) == 6 - 1 + 3


def test_rebels_win_when_king_dies():
    eng = start_engine(sha_hands())
    eng.king.hp = 1
    pass_play_and_discard(eng)          # a 弃到 1 张
    assert eng.pending.player == 'b'
    play_sha(eng, 'b', 'a')             # b（反贼）杀主公，a 无闪直接濒死
    assert eng.winner == IDENTITY['rebel']
    with pytest.raises(IllegalAction):
        eng.apply(Pass('a'))


def test_king_kills_minister_punish():
    """主公杀死忠臣：弃置主公所有牌（手牌+装备区），判定区不动。"""
    from isha.core.cards import make_card
    from isha.dict.card import CARD_NAME, CARD_SUIT
    eng = start_engine(sha_hands())
    king, minister = eng.king, eng.player('d')   # IDS5 中 d 是忠臣
    king.weapon = make_card(901, CARD_SUIT['spade'], '5', CARD_NAME['qinglong'],
                            spec='3')
    king.minus_horse = make_card(902, CARD_SUIT['heart'], '5', '赤兔', spec='-1')
    king.judgement.append(make_card(903, CARD_SUIT['heart'], '6',
                                    CARD_NAME['contentment']))
    hand_cids = {c.cid for c in king.hand}
    minister.hp = 1
    eng.pending = eng._play_ask(king)   # 白盒装装备后重建出牌询问（目标选项已固化）
    play_sha(eng, 'a', 'd')             # 主公杀忠臣，d 无闪阵亡
    assert not minister.alive
    assert king.hand == []              # 手牌清空
    assert king.equips() == []          # 装备区清空
    assert len(king.judgement) == 1     # 判定区不属于角色，保留
    assert king.alive and eng.winner is None
    assert hand_cids | {901, 902} <= {c.cid for c in eng.discard_pile}
    assert not any(c.cid == 903 for c in eng.discard_pile)


def test_king_side_win():
    eng = start_engine(sha_hands())
    for nick in ('b', 'c', 'e'):        # b/c 是反贼，e 是内奸
        eng.player(nick).hp = 1
    play_sha(eng, 'a', 'b')             # a 杀反贼 b
    pass_play_and_discard(eng)
    assert eng.pending.player == 'c'
    pass_play_and_discard(eng)          # c 结束 → d
    play_sha(eng, 'd', 'c')             # d（忠臣）杀反贼 c
    pass_play_and_discard(eng)
    assert eng.pending.player == 'e'
    pass_play_and_discard(eng)          # e 结束 → a
    play_sha(eng, 'a', 'e')             # a 杀内奸 e，反贼内奸全灭
    assert eng.winner == '主公阵营'


def test_traitor_sole_survivor_win():
    eng = start_engine(sha_hands())
    for nick in ('b', 'c', 'd'):        # 反贼、忠臣先死光，只剩主公与内奸
        victim = eng.player(nick)
        victim.hp = 0
        eng._death(victim, None)
    assert eng.winner is None
    eng._death(eng.king, None)
    assert eng.winner == IDENTITY['traitor']


# ---------- 超时与非法动作 ----------

def test_timeout_defaults_to_pass():
    hands = sha_hands()
    hands[1] = [SHAN, SHA, SHA, SHA]
    eng = start_engine(hands)
    play_sha(eng, 'a', 'b')
    effects = eng.timeout()             # b 超时默认不出闪
    assert 'damaged' in kinds(effects)
    assert eng.player('b').hp == 3


def test_timeout_play_phase_passes():
    eng = start_engine(sha_hands())
    eng.timeout()                       # a 出牌阶段超时 = 结束出牌
    assert eng.pending.kind == 'discard'


def test_wrong_player_rejected():
    eng = start_engine(sha_hands())
    with pytest.raises(IllegalAction):
        eng.apply(Pass('b'))            # 当前应行动的是 a


def test_unknown_card_rejected():
    eng = start_engine(sha_hands())
    with pytest.raises(IllegalAction):
        eng.apply(PlayCards('a', (9999,), 'b'))


def test_illegal_play_reasons():
    eng = start_engine(sha_hands())
    with pytest.raises(IllegalAction, match='你手里没有这张牌'):
        eng.apply(PlayCards('a', (9999,), 'b'))
    with pytest.raises(IllegalAction, match='一次只能使用一张牌'):
        eng.apply(PlayCards('a', (cid(eng, 'a', SHA, 0),
                                  cid(eng, 'a', SHA, 1)), 'b'))
    with pytest.raises(IllegalAction, match='目标不合法'):
        eng.apply(PlayCards('a', (cid(eng, 'a', SHA),), 'x'))
    play_sha(eng, 'a', 'b')                 # b 无闪命中，回到 a 的出牌
    with pytest.raises(IllegalAction, match='已经出过杀'):
        eng.apply(PlayCards('a', (cid(eng, 'a', SHA),), 'b'))


def test_response_reason():
    hands = sha_hands()
    hands[1] = [SHAN, SHA, SHA, SHA]
    eng = start_engine(hands)
    play_sha(eng, 'a', 'b')
    with pytest.raises(IllegalAction, match='只能打出这些牌'):
        eng.apply(PlayCards('b', (cid(eng, 'b', SHA),)))   # 杀不能当闪


def test_discard_reason():
    eng = start_engine(sha_hands())
    eng.apply(Pass('a'))                    # a 有 6 张，需弃 1 张
    assert eng.pending.kind == 'discard'
    with pytest.raises(IllegalAction, match='恰好弃置 1 张'):
        eng.apply(DiscardCards('a', ()))


def test_gain_card_random_position():
    """公开进手的牌（五谷挑选、顺手、借刀得武器）随机插入手牌位置。"""
    from isha.core.cards import make_card
    eng = start_engine(sha_hands())
    p = eng.player('b')
    at_end = 0
    for i in range(8):
        card = make_card(900 + i, '♠', 'A', SHA)
        eng.gain_card(p, card)
        if p.hand.index(card) == len(p.hand) - 1:
            at_end += 1
    assert 0 < at_end < 8                   # 有插入末尾的，但绝不总是末尾


def test_gain_card_shuffles_offturn_hand():
    """非本回合玩家获得牌时整手洗乱：原有手牌的相对顺序也会被打乱，
    旁观者无法凭"牌序未变"推算新牌位置。当前回合玩家（a）则只随机插入，
    不打乱其正在操作的手牌顺序。"""
    from isha.core.cards import make_card
    eng = start_engine(sha_hands())
    p = eng.player('b')                     # 当前回合玩家是 a
    before = [c.cid for c in p.hand]
    card = make_card(900, '♠', 'A', SHA)
    eng.gain_card(p, card)
    after = [c.cid for c in p.hand]
    assert sorted(after) == sorted(before + [900])
    assert [c for c in after if c != 900] != before   # 原手牌相对顺序被打乱

    king_before = [c.cid for c in eng.king.hand]
    eng.gain_card(eng.king, make_card(901, '♥', 'K', SHA))
    king_rest = [c for c in eng.king.hand if c.cid != 901]
    assert [c.cid for c in king_rest] == king_before   # 当前玩家原牌序不变


# ---------- 牌堆 ----------

def test_empty_deck_no_crash():
    eng = start_engine(sha_hands(), rest=[])
    assert eng.pending.kind == 'play'   # 摸牌阶段摸不到牌也能继续


def test_reshuffle_discard_into_deck():
    eng = start_engine(sha_hands(), rest=[SHA, SHA])
    eng.apply(Pass('a'))
    effects = eng.apply(eng.pending.default)   # a 弃 1 张；轮到 b 摸牌时触发洗回
    assert 'reshuffle' in kinds(effects)
    assert len(eng.player('b').hand) == 4 + 1

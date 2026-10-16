"""CLI 输入解析测试：出牌阶段"牌+目标"同行输入（如 "3 d"）。

覆盖乐不思蜀、过河拆桥、决斗、杀、顺手牵羊等需要目标的牌，
以及装备丈八蛇矛时同行输入不被吞掉的回归。
"""

import contextlib
import io

import pytest

from isha.core.actions import PlayCards
from isha.dict.card import CARD_NAME
from isha.game.cli import prompt
from tests.helpers import make_card, sha_hands, start_engine

SHA = CARD_NAME['sha']
CONTENTMENT = CARD_NAME['contentment']
DISMANTLE = CARD_NAME['dismantle']
DUEL = CARD_NAME['duel']
SNATCH = CARD_NAME['snatch']
ZHANGBA = CARD_NAME['zhangba']


def run_prompt(monkeypatch, eng, *lines):
    """用预置输入驱动一次 prompt，返回解析出的动作。"""
    it = iter(lines)
    monkeypatch.setattr('builtins.input', lambda *a: next(it))
    with contextlib.redirect_stdout(io.StringIO()):
        return prompt(eng, eng.pending)


def make_eng(names, zhangba=False):
    hands = sha_hands()
    hands[0] = names
    eng = start_engine(hands)
    if zhangba:
        eng.player('a').weapon = make_card(900, '♠', '3', ZHANGBA, spec='3')
        eng.pending = eng._play_ask(eng.player('a'))
    return eng


@pytest.mark.parametrize('name, index, target', [
    (CONTENTMENT, 3, 'd'),      # 乐不思蜀
    (DISMANTLE, 3, 'd'),        # 过河拆桥
    (DUEL, 3, 'd'),             # 决斗
    (SHA, 0, 'b'),              # 杀
    (SNATCH, 3, 'b'),           # 顺手牵羊
])
def test_inline_card_and_target(monkeypatch, name, index, target):
    """需要目标的牌都支持 "牌 目标" 一行输入。"""
    eng = make_eng([SHA, SHA, SHA, name])
    card = eng.player('a').hand[index]
    action = run_prompt(monkeypatch, eng, f'{index} {target}')
    assert action == PlayCards('a', (card.cid,), target)


def test_inline_target_by_index(monkeypatch):
    """目标也可以用可选目标列表中的序号给出。"""
    eng = make_eng([SHA, SHA, SHA, CONTENTMENT])
    targets = eng.pending.data['options'][eng.player('a').hand[3].cid]
    action = run_prompt(monkeypatch, eng, '3 2')
    assert action.target == targets[2]


def test_two_step_still_works(monkeypatch):
    """只给牌不给目标时，仍列出可选目标二次选择。"""
    eng = make_eng([SHA, SHA, SHA, CONTENTMENT])
    card = eng.player('a').hand[3]
    action = run_prompt(monkeypatch, eng, '3', 'd')
    assert action == PlayCards('a', (card.cid,), 'd')


def test_inline_target_with_zhangba(monkeypatch):
    """回归：装备丈八蛇矛时，"牌 目标" 不再被丈八分支吞掉。"""
    eng = make_eng([SHA, SHA, SHA, CONTENTMENT], zhangba=True)
    card = eng.player('a').hand[3]
    action = run_prompt(monkeypatch, eng, '3 d')      # 乐不思蜀
    assert action == PlayCards('a', (card.cid,), 'd')
    sha = eng.player('a').hand[0]
    action = run_prompt(monkeypatch, eng, '0 b')      # 普通杀
    assert action == PlayCards('a', (sha.cid,), 'b')


def test_zhangba_two_cards_as_sha(monkeypatch):
    """丈八蛇矛原有用法不受影响：两张牌当杀，目标同行或后补。"""
    eng = make_eng([SHA, SHA, SHA, CONTENTMENT], zhangba=True)
    c0, c1 = eng.player('a').hand[0], eng.player('a').hand[1]
    action = run_prompt(monkeypatch, eng, '0 1 b')
    assert action == PlayCards('a', (c0.cid, c1.cid), 'b')
    action = run_prompt(monkeypatch, eng, '0 1', 'd')   # 目标后补
    assert action == PlayCards('a', (c0.cid, c1.cid), 'd')


def test_inline_target_applies_to_engine(monkeypatch):
    """解析出的动作能被引擎接受：乐不思蜀置入目标判定区。"""
    eng = make_eng([SHA, SHA, SHA, CONTENTMENT])
    action = run_prompt(monkeypatch, eng, '3 d')
    eng.apply(action)
    assert [c.name for c in eng.player('d').judgement] == [CONTENTMENT]


def test_borrow_sha_zhangba_two_cards_input(monkeypatch):
    """借刀杀人响应窗口：有丈八蛇矛时可输入两张手牌当杀（"0 2"）。"""
    hands = sha_hands()
    hands[0] = [CARD_NAME['borrow'], SHA, SHA, SHA]
    hands[1] = [CARD_NAME['shan'], CARD_NAME['shan'],
                CARD_NAME['peach'], CARD_NAME['shan']]
    eng = start_engine(hands)
    eng.player('b').weapon = make_card(900, '♠', '3', ZHANGBA, spec='3')
    eng.pending = eng._play_ask(eng.king)
    eng.apply(PlayCards('a', (eng.player('a').hand[0].cid,), 'b'))
    eng.apply(PlayCards('a', (), 'c'))          # 指定 b 杀 c
    assert eng.pending.kind == 'borrow_sha' and eng.pending.data['zhangba']
    b = eng.player('b')
    action = run_prompt(monkeypatch, eng, '0 2')
    assert action == PlayCards('b', (b.hand[0].cid, b.hand[2].cid))
    eng.apply(action)                           # 虚拟杀命中无闪的 c
    assert eng.player('c').hp == 3
    assert b.weapon is not None

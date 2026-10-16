"""Web 前端层测试：状态字段（距离/装备详情）、身份可见性、生命周期与自动超时。"""

import json
import time

from isha.game.web import Game

IDS = {'主公', '忠臣', '反贼', '内奸'}


# ---------- 生命周期 ----------

def test_default_no_game():
    g = Game(timeout_secs=0)
    assert g.engine is None
    assert g.state()['active'] is False


def test_start_activates_game():
    g = Game(timeout_secs=0)
    g.start(5, seed=1)
    assert g.state()['active'] is True


def test_idle_close():
    g = Game(timeout_secs=0, idle_timeout=1)
    g.start(5, seed=1)
    g.last_activity -= 2   # 模拟闲置超时
    g.touch()
    assert g.engine is None
    assert g.state()['active'] is False
    assert any('自动关闭' in line for line in g.log)


def test_apply_without_game_rejected():
    import pytest

    from isha.core.engine import IllegalAction
    g = Game(timeout_secs=0)
    with pytest.raises(IllegalAction):
        g.apply({'type': 'pass'})


# ---------- 身份可见性 ----------

def test_you_identity_and_winner_reveal():
    g = Game(timeout_secs=0)
    g.start(5, seed=1)
    s = g.state()
    cur = s['pending']['player']
    assert s['you']['nick'] == cur
    assert s['you']['identity'] in IDS            # 行动者可见自己身份
    others = [p for p in s['players']
              if p['nick'] != cur and p['identity'] != '主公']
    assert all(p['identity'] == '未知' for p in others)
    g.engine._game_over('反贼')                   # 白盒：直接结束游戏
    s = g.state()
    assert all(p['identity'] in IDS for p in s['players'])   # 结束全亮


# ---------- 状态字段 ----------

def test_state_distance_field():
    g = Game(timeout_secs=0)
    g.start(5, seed=1)
    s = g.state()
    json.dumps(s, ensure_ascii=False)
    cur = s['pending']['player']
    for p in s['players']:
        if p['nick'] == cur:
            assert p['distance'] is None
        else:
            assert p['distance'] in (1, 2)   # 5 人局座位距离上限 2


def test_state_equip_detail():
    g = Game(timeout_secs=0)
    g.start(5, seed=1)
    from isha.core.cards import make_card
    g.engine.king.weapon = make_card(900, '♠', '5', '丈八蛇矛', spec='3')
    s = g.state()
    king = next(p for p in s['players'] if p['identity'] == '主公')
    assert king['equips'] == ['♠5丈八蛇矛（3）']


# ---------- 响应超时 ----------

def test_auto_timeout():
    g = Game(timeout_secs=1, idle_timeout=0)
    g.start(5, seed=1)
    first = g.engine.pending.player
    assert g.deadline is not None
    time.sleep(1.4)   # 等计时器触发：出牌阶段超时 = 结束出牌
    ask = g.engine.pending
    assert ask.kind != 'play' or ask.player != first
    assert any('超时' in line for line in g.log)


def test_timeout_disabled():
    g = Game(timeout_secs=0)
    g.start(5, seed=1)
    assert g.deadline is None
    assert g.state()['timeout_remaining'] is None

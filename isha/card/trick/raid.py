"""顺手牵羊 / 过河拆桥共用基类：由使用者选择目标的一张牌。

手牌为暗牌（Ask.data 中 label 为 None，按位置盲选）；
判定区与装备区为明牌（可直接选择，例如拆乐不思蜀、卸武器）。
"""

from isha.core.actions import PlayCards
from isha.core.asks import Ask
from isha.core.engine import Frame

from ..base import TrickRule


class RaidRule(TrickRule):
    max_distance = None   # None = 不限距离

    def play_targets(self, eng, p, card):
        targets = [q.nick for q in eng.alive()
                   if q is not p and (q.hand or q.judgement or q.equips())
                   and (self.max_distance is None
                        or eng.distance(p.nick, q.nick) <= self.max_distance)]
        return targets or None

    def effect(self, eng, source, card, action) -> Frame:
        target = eng.player(action.target)
        options = ([(c.cid, None) for c in target.hand]              # 手牌：暗牌
                   + [(c.cid, c.label) for c in target.judgement]    # 判定区：明牌
                   + [(c.cid, c.label) for c in target.equips()])    # 装备区：明牌
        if not options:
            return
        allowed = [cid for cid, _ in options]

        def check(act):
            if not isinstance(act, PlayCards) or len(act.cids) != 1:
                return '请选择一张牌'
            if act.cids[0] not in allowed:
                return '只能选择该角色的手牌或装备区中的一张牌'
            return True

        act = yield Ask(source.nick, 'choose_card',
                        {'trick': card.label, 'target': target.nick,
                         'cards': options},
                        check, default=PlayCards(source.nick, (options[0][0],)))
        chosen = act.cids[0]
        picked = target.find(chosen)
        if picked is not None:
            target.hand.remove(picked)
            hidden = True
        else:
            found = next(((i, c) for i, c in enumerate(target.judgement)
                          if c.cid == chosen), None)
            if found is not None:
                target.judgement.pop(found[0])
                picked = found[1]
            else:
                slot, picked = target.find_equip(chosen)
                setattr(target, slot, None)
            hidden = False
        self.gain(eng, source, target, picked, hidden)

    def gain(self, eng, source, target, card, hidden: bool):
        raise NotImplementedError

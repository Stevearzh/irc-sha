"""乐不思蜀（延时锦囊）：置入目标判定区；其判定阶段翻牌，不为红桃则跳过出牌阶段。

使用时仅置入判定区不结算；无懈可击的时机是判定阶段、翻判定牌之前（见 judge()）。
"""

from isha.core.engine import Frame
from isha.dict.card import CARD_NAME, CARD_SUIT

from ..base import TrickRule


class ContentmentRule(TrickRule):
    name = CARD_NAME['contentment']
    delayed = True

    def play_targets(self, eng, p, card):
        # 判定区已有乐不思蜀的角色不能再成为目标
        targets = [q.nick for q in eng.alive() if q is not p
                   and not any(c.name == self.name for c in q.judgement)]
        return targets or None

    def effect(self, eng, source, card, action):
        target = eng.player(action.target)
        target.judgement.append(card)
        eng.emit('trick_placed', label=card.label, nick=target.nick)

    def judge(self, eng, p, card) -> Frame:
        # 无懈可击窗口：判定牌翻开之前
        if (yield from eng.negation_window(p, card.label, p.nick)):
            eng.emit('negated', label=card.label, target=p.nick)
            eng.to_discard(card)
            return
        flip = eng.judge_flip(p, self.name)
        eng.to_discard(card)
        if flip is not None and flip.suit != CARD_SUIT['heart']:
            p.skip_play = True
            eng.emit('skip_play', nick=p.nick, reason=self.name)

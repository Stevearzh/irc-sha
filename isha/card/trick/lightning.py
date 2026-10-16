"""闪电（延时锦囊）：置入自己判定区；判定为黑桃 2-9 则受 3 点伤害，否则移给下家。

移动时跳过判定区已有闪电的玩家（官方裁定）；被无懈可击抵消同样移动。
"""

from isha.core.engine import Frame
from isha.dict.card import CARD_NAME, CARD_SUIT

from ..base import TrickRule


class LightningRule(TrickRule):
    name = CARD_NAME['lightning']
    delayed = True
    STRIKE_POINTS = {str(i) for i in range(2, 10)}

    def play_targets(self, eng, p, card):
        # 判定区已有闪电的玩家不能再挂
        if any(c.name == self.name for c in p.judgement):
            return None
        return []

    def effect(self, eng, source, card, action):
        source.judgement.append(card)
        eng.emit('trick_placed', label=card.label, nick=source.nick)

    def judge(self, eng, p, card) -> Frame:
        # 无懈可击窗口：判定牌翻开之前
        if (yield from eng.negation_window(p, card.label, p.nick)):
            eng.emit('negated', label=card.label, target=p.nick)
            self._move_on(eng, p, card)
            return
        flip = eng.judge_flip(p, self.name)
        if flip is not None and flip.suit == CARD_SUIT['spade'] \
                and flip.point in self.STRIKE_POINTS:
            eng.to_discard(card)
            yield from eng.damage(None, p, 3)   # 闪电伤害无来源
        else:
            self._move_on(eng, p, card)

    def _move_on(self, eng, p, card):
        nxt = eng.next_alive(p)
        while nxt is not None and any(c.name == self.name for c in nxt.judgement):
            nxt = eng.next_alive(nxt)   # 跳过已有闪电的玩家
            if nxt is p:                 # 全部下家都有闪电（极端情况）
                nxt = None
        if nxt is None:
            eng.to_discard(card)
            eng.emit('lightning_fizzle', label=card.label)
            return
        nxt.judgement.append(card)
        eng.emit('lightning_move', nick=nxt.nick)

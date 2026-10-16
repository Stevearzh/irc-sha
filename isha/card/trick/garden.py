"""桃园结义：所有存活玩家回复 1 点体力（满血无效）。

每名目标生效前单独开无懈可击窗口。
"""

from isha.core.engine import Frame
from isha.dict.card import CARD_NAME

from ..base import TrickRule


class GardenRule(TrickRule):
    name = CARD_NAME['garden']
    negate_whole = False

    def play_targets(self, eng, p, card):
        injured = [q for q in eng.alive() if q.hp < q.max_hp]
        return [] if injured else None

    def effect(self, eng, source, card, action) -> Frame:
        skip = set()   # Pass(rest=True) 的玩家：本张锦囊后续窗口不再询问
        for q in eng.seat_order_from(source):
            if eng.winner:
                return
            if q.hp >= q.max_hp:
                continue
            if (yield from eng.negation_window(source, card.label, q.nick,
                                               skip)):
                eng.emit('negated', label=card.label, target=q.nick)
                continue
            q.hp += 1
            eng.emit('healed', nick=q.nick, hp=q.hp)

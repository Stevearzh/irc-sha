"""五谷丰登：亮出等同于存活人数的牌，从使用者起依次挑选一张。

每名目标挑选前单独开无懈可击窗口；剩余未被挑选的牌置入弃牌堆。
"""

from isha.core.actions import PlayCards
from isha.core.asks import Ask
from isha.core.engine import Frame
from isha.dict.card import CARD_NAME

from ..base import TrickRule


class HarvestRule(TrickRule):
    name = CARD_NAME['harvest']
    negate_whole = False

    def play_targets(self, eng, p, card):
        return []

    def effect(self, eng, source, card, action) -> Frame:
        revealed = []
        for _ in range(len(eng.alive())):
            c = eng.draw_one()
            if c is None:
                break
            revealed.append(c)
        eng.emit('harvest_reveal',
                 labels=[c.label for c in revealed])

        skip = set()   # Pass(rest=True) 的玩家：本张锦囊后续窗口不再询问
        for q in eng.seat_order_from(source):
            if not revealed or eng.winner:
                break
            if (yield from eng.negation_window(source, card.label, q.nick,
                                               skip)):
                eng.emit('negated', label=card.label, target=q.nick)
                continue

            def check(act, revealed=list(revealed)):
                if not isinstance(act, PlayCards) or len(act.cids) != 1:
                    return '请选择一张亮出的牌'
                if act.cids[0] not in [c.cid for c in revealed]:
                    return '只能从亮出的牌中选择'
                return True

            act = yield Ask(q.nick, 'harvest',
                            {'revealed': [(c.cid, c.label) for c in revealed]},
                            check,
                            default=PlayCards(q.nick, (revealed[0].cid,)))
            chosen = next(c for c in revealed if c.cid == act.cids[0])
            revealed.remove(chosen)
            eng.gain_card(q, chosen)   # 明牌获得：进手时随机插入/洗乱，位置不泄露
            eng.emit('harvest_pick', nick=q.nick, label=chosen.label)

        for c in revealed:
            eng.to_discard(c)

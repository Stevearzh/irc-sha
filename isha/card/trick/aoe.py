"""南蛮入侵 / 万箭齐发共用基类：其余存活玩家依次需打出响应牌，否则受伤。

每个目标生效前单独开无懈可击窗口；万箭的响应是闪避（含八卦阵判定）。
"""

from isha.core.actions import PlayCards
from isha.core.engine import Frame

from ..base import SHAN, TrickRule, dodge_window, others


class AoeRule(TrickRule):
    response_name = None
    negate_whole = False

    def play_targets(self, eng, p, card):
        return [] if others(eng, p) else None

    def effect(self, eng, source, card, action) -> Frame:
        skip = set()   # Pass(rest=True) 的玩家：本张锦囊后续窗口不再询问
        for q in eng.seat_order_from(source):
            if eng.winner:
                return
            if q is source or not q.alive:
                continue
            if (yield from eng.negation_window(source, card.label, q.nick,
                                               skip,
                                               response=self.response_name)):
                eng.emit('negated', label=card.label, target=q.nick)
                continue
            if self.response_name == SHAN:
                # 万箭齐发：闪避窗口含八卦阵判定
                if (yield from dodge_window(eng, source, q, card.label)):
                    continue
            else:
                cards = [c for c in q.hand if c.name == self.response_name]
                if cards:
                    act = yield eng.card_response_ask(
                        q.nick, 'respond_aoe', cards,
                        {'source': source.nick, 'trick': card.label,
                         'response': self.response_name})
                    if isinstance(act, PlayCards):
                        used = eng.play_card(q, act.cids[0])
                        eng.emit('responded', nick=q.nick, label=used.label)
                        continue
            yield from eng.damage(source, q, 1)

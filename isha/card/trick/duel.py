"""决斗：双方轮流出杀，先不出者受到对方造成的 1 点伤害。"""

from isha.core.actions import PlayCards
from isha.core.engine import Frame
from isha.dict.card import CARD_NAME

from ..base import SHA, TrickRule, others


class DuelRule(TrickRule):
    name = CARD_NAME['duel']
    response_name = SHA

    def play_targets(self, eng, p, card):
        return others(eng, p)

    def effect(self, eng, source, card, action) -> Frame:
        responder, other = eng.player(action.target), source
        while True:
            shas = [c for c in responder.hand if c.name == SHA]
            if shas:
                act = yield eng.card_response_ask(
                    responder.nick, 'duel', shas, {'other': other.nick})
                if isinstance(act, PlayCards):
                    used = eng.play_card(responder, act.cids[0])
                    eng.emit('responded', nick=responder.nick, label=used.label)
                    responder, other = other, responder
                    continue
            yield from eng.damage(other, responder, 1)
            return

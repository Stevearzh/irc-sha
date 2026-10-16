"""桃：出牌阶段对自己使用回复 1 点体力；濒死时亦可打出救人。"""

from ..base import BASIC, PEACH


class PeachRule:
    name = PEACH
    type = BASIC

    def play_targets(self, eng, p, card) -> list[str] | None:
        return [] if p.hp < p.max_hp else None

    def resolve(self, eng, source, card, action):
        eng.play_card(source, card.cid)
        source.hp += 1
        eng.emit('card_used', nick=source.nick, label=card.label, target=None)
        eng.emit('healed', nick=source.nick, hp=source.hp)

"""过河拆桥：弃置任意一名玩家的一张牌（弃置后公开）。"""

from isha.dict.card import CARD_NAME

from .raid import RaidRule


class DismantleRule(RaidRule):
    name = CARD_NAME['dismantle']

    def gain(self, eng, source, target, card, hidden):
        eng.to_discard(card)
        eng.emit('dismantle', nick=source.nick, target=target.nick,
                 label=card.label)

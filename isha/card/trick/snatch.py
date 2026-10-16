"""顺手牵羊：获得距离 1 以内一名玩家的一张牌（手牌暗抽不公开）。"""

from isha.dict.card import CARD_NAME

from .raid import RaidRule


class SnatchRule(RaidRule):
    name = CARD_NAME['snatch']
    max_distance = 1

    def gain(self, eng, source, target, card, hidden):
        eng.gain_card(source, card)   # 进手时随机插入/洗乱，位置不泄露来源
        eng.emit('snatch', nick=source.nick, target=target.nick,
                 label=None if hidden else card.label)

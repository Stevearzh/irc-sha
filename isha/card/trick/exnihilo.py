"""无中生有：摸两张牌。"""

from isha.dict.card import CARD_NAME

from ..base import TrickRule


class ExNihiloRule(TrickRule):
    name = CARD_NAME['exnihilo']

    def play_targets(self, eng, p, card):
        return []

    def effect(self, eng, source, card, action):
        eng.draw(source, 2)

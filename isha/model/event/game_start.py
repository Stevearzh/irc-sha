from isha.core.event import event
from isha.dict.event import EVENT
from .card_shuffle import card_shuffle
from .card_deal import four_card_deal

class event_game_start(event):
    def __init__(self):
        event.__init__(self, EVENT['game_start'], self.__effect)

    def __effect(self, table, source=None):
        card_shuffle(table)
        list(map(lambda player: four_card_deal(player, table), table.players()))

game_start = event_game_start()

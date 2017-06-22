from isha.core.event import event
from isha.dict.event import EVENT
from .card_shuffle import card_shuffle
from .set_max_hp import set_max_hp
from .card_deal import four_card_deal

class event_game_start(event):
    def __init__(self):
        event.__init__(self, EVENT['game_start'], self.__effect)

    def __effect(self, table, source=None):
        card_shuffle(table)
        list(map(lambda player: self.__init_defs(player, table, max_hp=4), table.players()))

    def __init_defs(self, player, table, max_hp):
        four_card_deal(player, table)       # deal each player four cards
        set_max_hp(player, table, max_hp)   # set initial hp for each player

game_start = event_game_start()

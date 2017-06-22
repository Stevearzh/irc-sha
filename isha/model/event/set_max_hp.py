from isha.core.event import event
from isha.dict.event import EVENT
from isha.dict.identity import IDENTITY

class event_set_max_hp(event):
    def __init__(self):
        event.__init__(self, EVENT['set_max_hp'], self.__effect)

    def __effect(self, player, table, max_hp):
        if len(table.players()) >= 5 and player.id() == IDENTITY['king']:
            player.set_initial_hp(max_hp + 1)
        else:
            player.set_initial_hp(max_hp)

set_max_hp = event_set_max_hp()

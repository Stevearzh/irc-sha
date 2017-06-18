from isha.core.event import event
from isha.dict.event import EVENT

class card_deal(event):
    def __init__(self):
        event.__init__(self, EVENT['card_deal'], self.__effect)

    def __effect(self, player, table):
        player.get_card(table.deal_card())

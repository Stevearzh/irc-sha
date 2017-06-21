from isha.core.event import event
from isha.dict.event import EVENT

class n_card_deal(event):
    def __init__(self, n):
        event.__init__(self, EVENT['card_deal'], self.__effect)
        self.__n = n

    def __effect(self, player, table):
        list(map(lambda i: player.get_card(table.deal_card()), list(range(self.__n))))

common_card_deal = n_card_deal(1)
two_card_deal    = n_card_deal(2)
four_card_deal   = n_card_deal(4)

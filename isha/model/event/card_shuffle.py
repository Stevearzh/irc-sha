from isha.dict.event import EVENT
from isha.core.event import event

class event_card_shuffle(event):
    def __init__(self):
        event.__init__(self, EVENT['card_shuffle'], self.__effect)

    def __effect(self, table, source=None):
        table.shuffle_card()

card_shuffle = event_card_shuffle()

from isha.core.event import event
from isha.dict.event import EVENT

class event_card_used(event):
    def __init__(self):
        event.__init__(self, EVENT['card_used'], self.__effect)

    def __effect(self, table, card, from_whom, to_whom=None):
        if card.need_target() and to_whom == None:
            return False
        else:
            table.judge(EVENT['card_used'], card, from_whom, to_whom)

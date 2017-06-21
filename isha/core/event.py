from isha.dict.event import EVENT

class event:
    def __init__(self, type, effect):
        self.__type   = type
        self.__effect = effect

        if not self.__type in list(EVENT.values()):
            self.__type = EVENT['unknown']

    def type(self):
        return self.__type

    def __call__(self, target, source=None):
        return self.__effect(target, source)

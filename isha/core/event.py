from isha.dict.event import EVENT

class event:
    def __init__(self, type, effect):
        self.__type   = type
        self.__effect = effect

        try:
            list(EVENT.values()).index(self.__type)
        except Exception as e:
            self.__type = EVENT['unknown']

    def show_type(self):
        return self.__type

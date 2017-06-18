from isha.dict.event import EVENT

class event:
    def __init__(self, type, effect):
        self.__type   = type
        self.__effect = effect

        if not self.__type in list(EVENT.values()):
            self.__type = EVENT['unknown']

    def type(self):
        return self.__type

    def effect(self, target, source):
        return self.__effect(target, source)

class event_system:
    def __init__(self):
        self.__listeners = {}

    def on(self, event, func):
        if event in self.__listeners:
            self.__listeners[event].append(func)
        else:
            self.__listeners[event] = [func]

    def trigger(self, event):
        if event in self.__listeners:
            for func in self.__listeners[event]:
                func()

class broadcast(list):
    def __call__(self, *args, **kwargs):
        for f in self:
            f(*args, **kwargs)

    def __repr__(self):
        return 'Broadcast(%s)' % list.__repr__(self)

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


class Event(object):
    pass

class QuackEvent(Event):
    pass

class LinesDeletedEvent(Event):
    def __init__(self, number_of_lines=1):
        self.number_of_lines = number_of_lines

class OpponentKnockedOutEvent(Event):
    pass

class GameStartedEvent(Event):
    pass

class CardsController(object):
    def winner(self):
        return ['Hearts']

class PlayerController(object):
    def winning(self):
        return False

class AceController(object):
    def beats_hearts(self):
        return False

class HeartsController(object):
    def beats_aces(self):
        return True

    def give_me_love(self):
        return '<3'

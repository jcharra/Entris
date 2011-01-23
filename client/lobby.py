
import httplib
import logging
from statewindows import StateWindow
from config import GAME_SERVER, SCREEN_DIMENSIONS

class Lobby(StateWindow):
    def __init__(self, dimensions=SCREEN_DIMENSIONS):
        StateWindow.__init__(self, dimensions)
        self.game_list = []
        
    def get_game_data(self):
        try:
            connection = httplib.HTTPConnection(GAME_SERVER)
            connection.request("GET", "/list")
            data = self.connection.getresponse().read()
            # 72549,4,[]|17572,3,[]|7321,4,[]|46904,5,[]|63021,2,[]
            games = data.split("|")
            
            self.game_data = {}
            for game in games:
                # use json to deserialize objects here!
                pass
                
        except Exception, msg:
            logging.warn("Error connecting to server: %s" % msg)
            return []
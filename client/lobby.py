
import httplib
import logging
import json

from statewindows import StateWindow
from config import GAME_SERVER, SCREEN_DIMENSIONS
from pygame.locals import K_r

class Lobby(StateWindow):
    def __init__(self, dimensions=SCREEN_DIMENSIONS):
        StateWindow.__init__(self, dimensions)
        self.games = []
        self.get_game_data()
        
    def get_game_data(self):
        try:
            connection = httplib.HTTPConnection(GAME_SERVER)
            connection.request("GET", "/list")
            data = connection.getresponse().read()
            self.games = json.loads(data)
        except Exception, msg:
            logging.warn("Error connecting to server: %s" % msg)
    
    def handle_keypress(self, key):
        if key == K_r:
            self.get_game_data()
        else:
            StateWindow.handle_keypress(self, key)
            
    def render(self, screen):
        screen.fill((0, 0, 0))
        
        header_img = self.font.render('Online Games', 1, self.font_color)
        header_pos = header_img.get_rect()
        header_pos.centerx = self.get_rect().centerx
        header_pos.centery = 30
        screen.blit(header_img, header_pos)
    
        top_offset = 50
        item_height = (self.get_height() - top_offset)/(len(self.games) + 2)
        
        for idx, game in enumerate(self.games):
            text_img = self.font.render(game['game_id'], 1, self.font_color)
            text_pos = text_img.get_rect()
            text_pos.centerx = self.get_rect().centerx
            text_pos.centery = top_offset + idx*item_height
            screen.blit(text_img, text_pos)    
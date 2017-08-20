
try:
    import httplib as http
except ImportError:
    import http.client as http

try:
    import json
except ImportError:
    import simplejson as json

import logging
import codecs

from pygame.locals import K_r, K_RETURN, K_UP, K_DOWN

from statewindows import StateWindow
from config import SCREEN_DIMENSIONS, MAX_NUMBER_OF_GAMES
from networking import DEFAULT_SERVER

logger = logging.getLogger("lobby")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


class Lobby(StateWindow):
    
    column_headings = ("Grid size", "Duck probability", "Players", "Free slots")
    DEFAULT_SUBTITLE = "Select a game to join - press 'R' to refresh list"
    
    def __init__(self, dimensions=SCREEN_DIMENSIONS):
        """
        The layout is organized in rows like this
        
        **********************
        ********TITLE*********
        **********************
        ****COLUMN HEADINGS***
        ******GAME1 DATA******
        ******GAME1 DATA******
        ******GAME1 DATA******
        ...
        ******GAME25 DATA*****
        **********************
        ********SUBTITLE******
        """
        
        StateWindow.__init__(self, dimensions)

        self.row_height = self.get_height()/float(MAX_NUMBER_OF_GAMES + 5)
        self.column_width = self.get_width()/float(len(self.column_headings))
        self.first_column_center = self.column_width/2.0
        
        self.title_y_offset = self.row_height
        self.column_headings_y_offset = self.row_height*3
        self.game_list_y_offset = self.row_height*4
        self.subtitle_y_offset = self.get_height() - self.row_height 
        
        self.game_configs = []
        self.selected_index = 0
        self.subtitle = self.DEFAULT_SUBTITLE

        # Function that will yield the lobby's server address
        self.server_info_func = lambda: None

        self.response_reader = codecs.getreader("utf-8")
        
    def get_game_data(self):
        try:
            server_address = self.server_info_func() or DEFAULT_SERVER
            if ":" in server_address:
                host, port = server_address.split(":")
                connection = http.HTTPConnection(host, int(port))
            else:
                connection = http.HTTPConnection(server_address)

            connection.request("GET", "/list")
            resp_json = json.load(self.response_reader(connection.getresponse()))

            # Read response and filter out started 
            # games (as we cannot join those anymore)
            games = {gid: game for gid, game in resp_json.items()
                     if not game['started']}

            self.game_configs = sorted(games.values(), key=lambda g: g['game_id'])
        except Exception as ex:
            logger.error(ex)
            self.subtitle = "Error connecting to server"
    
    def as_dict(self):
        return self.game_configs[self.selected_index]

    def handle_keypress(self, event):
        key = event.key

        # Any key will cause the default subtitle to reappear
        self.subtitle = self.DEFAULT_SUBTITLE
        
        if key == K_r:
            # Refresh game list
            self.get_game_data()
        elif key == K_RETURN:
            if self.game_configs:
                self.finished = True
        elif key in (K_UP, K_DOWN):
            if self.game_configs:
                direction = 1 if key == K_DOWN else -1
                self.selected_index = (self.selected_index+direction) % len(self.game_configs)
        else:
            StateWindow.handle_keypress(self, event)
    
    def render_row(self, screen, items, y_offset, color):
        for idx, item in enumerate(items):
            text_img = self.font.render(str(item), 1, color)
            text_pos = text_img.get_rect()
            text_pos.centerx = self.first_column_center + idx * self.column_width
            text_pos.top = y_offset
            screen.blit(text_img, text_pos)    
        
    def render_selection_bar(self, screen):
        if self.game_configs:
            y_offset = self.game_list_y_offset + self.selected_index * self.row_height
            screen.fill(self.selection_bar_color, 
                        (0, y_offset, self.get_width(), self.row_height))
        
    @staticmethod
    def _repr_for_display(game):
        """
        Build a list of items suitable for display in the game
        selection list, getting the corresponding data from the
        game instance.
        """

        dims = "{}x{}".format(game["width"], game["height"])
        duckprob = "%i%%" % int(100 * game["duck_prob"])
        player_names = [p['player_id'] for p in game["screen_names"]]
        names = ",".join(player_names or ("None yet",))
        freeslots = int(game["size"]) - len(game["screen_names"])

        return dims, duckprob, names, freeslots
    
    def render_subtitle(self, screen):
        text_img = self.font.render(self.subtitle, 1, self.hint_color)
        text_pos = text_img.get_rect()
        text_pos.centerx = self.get_rect().centerx
        text_pos.top = self.subtitle_y_offset
        screen.blit(text_img, text_pos)    
    
    def render(self, screen):
        screen.fill((0, 0, 0))
        
        header_img = self.font.render('Online Games', 1, self.font_color)
        header_pos = header_img.get_rect()
        header_pos.centerx = self.get_rect().centerx
        header_pos.top = self.title_y_offset
        screen.blit(header_img, header_pos)
    
        self.render_row(screen, 
                        self.column_headings, 
                        self.column_headings_y_offset, 
                        self.hint_color)
    
        self.render_selection_bar(screen)
        self.render_subtitle(screen)
    
        for idx, game in enumerate(self.game_configs):
            items = self._repr_for_display(game)
            y_offset = self.game_list_y_offset + idx * self.row_height
            self.render_row(screen, items, y_offset, self.font_color)



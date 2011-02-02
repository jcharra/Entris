
import pygame
from monitoring import GameMonitor

class InfoPanel(pygame.Surface):
    """
    The window on the right of the game screen showing
    the current score and the next piece.
    """
    
    def __init__(self, dimensions, game):
        self.dimensions = dimensions
        pygame.Surface.__init__(self, dimensions)
        
        self.game = game
        self.block_size = self.get_width()/10
        
        self.font_color = (0, 200, 0)
        self.font = pygame.font.Font('jack_type.ttf', 18)
        
        # Keep track of players that have been in the game
        self.players_at_game_start = {}
        
    def render_base(self):
        # background
        self.fill((70, 70, 70))
        self.render_preview()
        
    def renderSinglePlayerScreen(self):
        self.render_base()
        self.render_level()
        self.render_score()
    
    def renderMultiPlayerScreen(self):    
        self.render_base()
        self.render_game_id()
        self.render_players()
        
        if not self.players_at_game_start and self.game.started:
            # Make a snapshot of the players that 
            # are alive at the beginning
            self.players_at_game_start = self.game.listener.players

    def render_game_id(self):
        text_img = self.font.render("Game %s" % self.game.listener.game_id, 1, (127, 127, 0))
        text_pos = text_img.get_rect()
        text_pos.centerx = self.get_rect().centerx
        text_pos.centery = 200
        self.blit(text_img, text_pos)
            
    def render_score(self):
        text_img = self.font.render("Score", 1, self.font_color)
        text_pos = text_img.get_rect()
        text_pos.centerx = self.get_rect().centerx
        text_pos.centery = 300
        self.blit(text_img, text_pos)

        text_img = self.font.render("%09i" % self.game.score, 1, self.font_color)
        text_pos = text_img.get_rect()
        text_pos.centerx = self.get_rect().centerx
        text_pos.centery = 370
        self.blit(text_img, text_pos)
    
    def render_level(self):
        text_img = self.font.render("Level %s" % self.game.level, 
                                    1, self.font_color)
        text_pos = text_img.get_rect()
        text_pos.centerx = self.get_rect().centerx
        text_pos.centery = 250
        self.blit(text_img, text_pos)
    
    def render_players(self):
        """
        Renders the players and their respective game monitors.
        TODO: Refactor me!
              Avoid instantiating a Monitor object on each call
              => implement a monitors dictionary, keeping the player
              ids as keys and monitor objects as values.
        """
        
        # Iterate over all players that started the game.
        # If the game has not started, this list will be empty,
        # so use the list of players that are currently registered
        # in the game instance.
        player_list_for_display = (self.players_at_game_start 
                                   or self.game.listener.players)
        
        # We need monitors for each opponent
        number_of_monitors = self.game.listener.game_size - 1
        
        # Determine width of the monitor. Only if there is 
        # just one opponent, we use the entire width available
        player_monitor_width = (self.get_width() - 4
                                if number_of_monitors == 1
                                else self.get_width() / 2 - 4)
        
        vertical_remainder = self.get_height() - 230
        number_of_monitor_rows = (number_of_monitors+1)/2 
        player_monitor_height = vertical_remainder/number_of_monitor_rows - 4
        
        # Filter out our own id ... no need to monitor ourselves
        opponent_ids = [pid for pid in player_list_for_display.keys() 
                        if pid != self.game.listener.player_id]
         
        for idx in range(number_of_monitors):
            x_start = (idx % 2) * (player_monitor_width + 2) + 2
            y_start = 230 + (idx / 2) * (player_monitor_height + 2)
            
            opp_id = opponent_ids[idx] if idx < len(opponent_ids) else None            
            player_game_snapshot = self.game.listener.player_game_snapshots.get(opp_id)
            player_alive = opp_id in self.game.listener.players
            player_name = player_list_for_display.get(opp_id)
            
            monitor = GameMonitor((player_monitor_width, player_monitor_height))
            monitor.render_game(player_game_snapshot, 
                                player_name, 
                                player_alive=player_alive)
            
            self.blit(monitor, (x_start, y_start))                
            
    def render_preview(self):
        text_img = self.font.render("Next", 1, self.font_color)
        text_pos = text_img.get_rect()
        text_pos.centerx = self.get_rect().centerx
        text_pos.centery = 20
        self.blit(text_img, text_pos)

        if not self.game.piece_queue:
            return

        next_piece = self.game.piece_queue[0]
        next_piece_width = len(next_piece[0])
        
        x_offset = self.block_size * (5 - next_piece_width/2)
        y_offset = 50
        
        for row_index, row in enumerate(next_piece):
            for idx, color in enumerate(row):
                if not color:
                    continue
                
                x = x_offset + idx * self.block_size
                y = y_offset + row_index * self.block_size
                    
                rect = pygame.Rect((x, y), (self.block_size, self.block_size))
                self.fill((0, 255, 0), rect)
        
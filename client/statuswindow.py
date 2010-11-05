
import pygame
from monitoring import GameMonitor

class StatusWindow(pygame.Surface):
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
        player_list_font = pygame.font.Font('jack_type.ttf', 14)
        player_missing_font = pygame.font.Font('jack_type.ttf', 36)
        
        # Iterate over all players that started the game.
        # If the game has not started, this list will be empty,
        # so use the list of players that are currently registered
        # in the game instance.
        player_list_for_display = self.players_at_game_start or self.game.listener.players
        
        # Divide the remaining space evenly
        # for the 2x2 opponent monitors.
        vertical_remainder = self.get_height() - 230
        player_monitor_height = vertical_remainder/2 - 2
        player_monitor_width = self.get_width()/2 - 2
        
        player_ids = player_list_for_display.keys()
        for idx in range(4):
            x_start = (idx % 2) * (player_monitor_width + 1) + 1
            y_start = 230 + (idx / 2) * (player_monitor_height + 1)
            
            # Black background
            self.fill((0, 0, 0), pygame.Rect(x_start, y_start, 
                                             player_monitor_width,
                                             player_monitor_height))
            
            try:
                player_id = player_ids[idx]
                player_game_snapshot = self.game.listener.player_game_snapshots[player_id]
                
                # Paint deceased players gray ... others coloured
                color = self.font_color if player_id in self.game.listener.players else (50, 50, 50)
                
                player_name = player_list_for_display.get(player_id)
                
                monitor = GameMonitor((player_monitor_width, player_monitor_height))
                monitor.render_game(player_game_snapshot)
                self.blit(monitor, (x_start, y_start))
                
                t_img = player_list_font.render(player_name, 1, color)
                t_pos = t_img.get_rect()
                t_pos.left = x_start + 5
                t_pos.top = y_start
                
                self.blit(t_img, t_pos)
            except IndexError:
                # Not enough players present yet ... never mind.
                # Show a black box if we're expecting someone
                # to fill in this empty slot, or a red cross
                # otherwise
                if idx >= self.game.listener.game_size:
                    # Draw red cross
                    pygame.draw.aaline(self, (100, 0, 0), 
                                     (x_start, y_start), 
                                     (x_start + player_monitor_width,
                                      y_start + player_monitor_height))
                    pygame.draw.aaline(self, (100, 0, 0), 
                                     (x_start, y_start + player_monitor_height), 
                                     (x_start + player_monitor_width, y_start))
                else:
                    # Draw question mark
                    question_mark_img = player_missing_font.render("?", 1, (200, 0, 0))
                    qm_pos = question_mark_img.get_rect()
                    qm_pos.centerx = x_start + player_monitor_width / 2
                    qm_pos.centery = y_start + player_monitor_height / 2
                    self.blit(question_mark_img, qm_pos)
            
    def render_preview(self):
        text_img = self.font.render("Next", 1, self.font_color)
        text_pos = text_img.get_rect()
        text_pos.centerx = self.get_rect().centerx
        text_pos.centery = 20
        self.blit(text_img, text_pos)

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
        
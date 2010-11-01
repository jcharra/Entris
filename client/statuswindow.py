
import pygame

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
        player_list_font = pygame.font.Font('jack_type.ttf', 14)
        
        # Iterate over all players that started the game.
        # If the game has not started, this list will be empty,
        # so use the list of players stored in the game instance.
        player_list_for_display = self.players_at_game_start or self.game.listener.players
        
        # Divide the remaining space evenly
        # for the list of opponents.
        vertical_remainder = self.get_height() - 230
        player_monitor_height = vertical_remainder/2 - 2
        player_monitor_width = self.get_width()/2 - 2
        
        for idx, player_id in enumerate(player_list_for_display.keys()):
            # Paint deceased players gray ... others coloured
            color = self.font_color if player_id in self.game.listener.players else (50, 50, 50)
            
            player_name = self.players_at_game_start.get(player_id)
            
            x_start = (idx % 2) * player_monitor_width + 1
            y_start = 230 + (idx / 2) * player_monitor_height + 1
            
            t_img = player_list_font.render(player_name, 1, color)
            t_pos = t_img.get_rect()
            t_pos.left = x_start + 5
            t_pos.top = y_start
            
            monitor = pygame.Surface((player_monitor_width, player_monitor_height))
            monitor.fill((idx*75, idx*75, idx*75))
            self.blit(monitor, (x_start, y_start))
            self.blit(t_img, t_pos)
        
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
        

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
        player_list_font = pygame.font.Font('jack_type.ttf', 18)
        # Iterate over all players that started the game.
        # If the game has not started, this list will be empty,
        # so use the list of players stored in the game instance.
        player_list_for_display = self.players_at_game_start or self.game.listener.players
        for idx, player_id in enumerate(player_list_for_display.keys()):
            # Paint deceased players gray ... others coloured
            color = self.font_color if player_id in self.game.listener.players else (50, 50, 50)
            
            # TODO: Display miniature view of snapshot here
            snapshot_length = len(self.game.listener.player_game_snapshots.get(player_id, ''))
            player_name = self.game.listener.players.get(player_id)
            
            t_img = player_list_font.render("%s %s" % (player_name, snapshot_length), 1, color)
            t_pos = t_img.get_rect()
            t_pos.centerx = self.get_rect().centerx
            t_pos.centery = 230 + idx * 24
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
        
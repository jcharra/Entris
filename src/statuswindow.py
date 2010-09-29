
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
        self.font = pygame.font.Font(None, 24)
    
    def render_base(self):
        # background
        self.fill((70, 70, 70))
        self.render_preview()
        
    def renderSinglePlayerScreen(self):
        self.render_base()
        self.render_level()
        self.render_score()
    
    def renderMultiPlayerScreen(self, game_id, players):    
        self.render_base()
        self.render_game_id(game_id)
        self.render_players(players)

    def render_game_id(self, game_id):
        text_img = self.font.render("Game %s" % game_id, 1, (127, 127, 0))
        text_pos = text_img.get_rect()
        text_pos.centerx = self.get_rect().centerx
        text_pos.centery = 380
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
    
    def render_players(self, players):
        text_img = self.font.render("Players in game:", 1, self.font_color)
        text_pos = text_img.get_rect()
        text_pos.centerx = self.get_rect().centerx
        text_pos.centery = 200
        self.blit(text_img, text_pos)
        
        for idx, player in enumerate(players):
            t_img = self.font.render(str(player), 1, self.font_color)
            t_pos = t_img.get_rect()
            t_pos.centerx = self.get_rect().centerx
            t_pos.centery = 230 + idx * 30
            self.blit(t_img, t_pos)
        
    def render_preview(self):
        text_img = self.font.render("Next", 1, self.font_color)
        text_pos = text_img.get_rect()
        text_pos.centerx = self.get_rect().centerx
        text_pos.centery = 50
        self.blit(text_img, text_pos)

        next_piece = self.game.piece_queue[0]
        next_piece_width = len(next_piece[0])
        
        x_offset = self.block_size * (5 - next_piece_width/2)
        y_offset = 100
        
        for row_index, row in enumerate(next_piece):
            for idx, color in enumerate(row):
                if not color:
                    continue
                
                x = x_offset + idx * self.block_size
                y = y_offset + row_index * self.block_size
                    
                rect = pygame.Rect((x, y), (self.block_size, self.block_size))
                self.fill((0, 255, 0), rect)
        
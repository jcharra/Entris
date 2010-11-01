import pygame
import logging

from statuswindow import StatusWindow
from messagelayover import TransparentLayover
from sound import SoundManager

logger = logging.getLogger("gamewindow")
handler = logging.StreamHandler()
logger.setLevel(logging.DEBUG)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

class GameWindow(pygame.Surface):
    """
    The game window is the visualization of the game instance it is
    responsible for, and controls how keyboard input is propagated to it.
    """
    
    def __init__(self, config, game_model):
        dimensions = config['screen_size']
        game_dimensions = config['game_size']
        
        self.dimensions = dimensions
        
        # The most important object for this instance:
        # The game we want to display
        self.game_model = game_model
        
        # cell width and height are floats
        self.cell_width = dimensions[0]/float(game_dimensions[0])
        self.cell_height = dimensions[1]/float(game_dimensions[1])
        
        pygame.Surface.__init__(self, self.dimensions)

        # A timer in milliseconds 
        self.clock = 0
        
        # The threshold (in milliseconds) indicating that the next step is due
        self.drop_interval = 500
        
        self.status_window = StatusWindow((self.get_width()*3/4, 
                                           self.get_height()), 
                                           self.game_model)
    
        self.message_layover = TransparentLayover(self)
    
        self.last_frame_before_death_rendered = False
    
        # Plug the into game a sound manager to get notified 
        # of sound-worthy events.
        self.sound_manager = SoundManager()
        self.game_model.add_observer(self.sound_manager)
        self.sound_manager.play_background_music()

    def get_total_width(self):
        return self.get_width() + self.status_window.get_width()
          
    def tear_down(self):
        self.sound_manager.stop_background_music()
        
    def update_view(self, screen):
        """
        Render self and status window. Screen object to
        draw on is passed as an argument.
        """
        
        self.render_game_window()
        screen.blit(self, (0, 0))

        self.render_status_window()
        screen.blit(self.status_window, (self.get_width(), 0))        
        
    def render_game_window(self):
        """
        Game may either be in state
        - over: display game over screen
        - won: display winner screen
        - waiting for other players: display waiting screen
        - in progress: display game
        """
        
        if self.game_model.gameover:
            # We may need to render one last frame
            if not self.last_frame_before_death_rendered:
                self.render_game()
                self.last_frame_before_death_rendered = True
            else:
                self.render_game_over_screen()
        elif self.game_model.victorious:
            self.render_winner_screen()
        elif not self.game_model.started:            
            self.render_waiting_screen()
        else:
            self.render_game()
            
    def render_status_window(self):
        """
        Render the status window depending on game type.
        """
        if self.game_model.listener:
            self.status_window.renderMultiPlayerScreen()
        else:
            self.status_window.renderSinglePlayerScreen()
    
    def render_game(self):
        """
        Visualizes the game model, i.e. paints the game grid
        """
        self.fill((0, 0, 0))        
        for idx, cell_value in enumerate(self.game_model.cells):
            if cell_value:
                # cell is filled with dead matter
                self.draw_cell(idx, cell_value)
            elif idx in self.game_model.moving_piece_indexes:
                # this cell is part of the moving piece
                self.draw_cell(idx, self.game_model.moving_piece.color)

    def draw_cell(self, index, color):
        """
        Draws a single cell in the grid with a given index (i.e. position)
        and the specified color.
        """
        
        top, left = divmod(index, self.game_model.column_nr)
        top = top * self.cell_height
        left = left * self.cell_width
        rect = pygame.Rect((left, top), (self.cell_width, self.cell_height))
        self.fill(color, rect)
        self.fill(self.darken(color), pygame.Rect((left, top), (self.cell_width, 2)))
        self.fill(self.darken(color), pygame.Rect((left, top), (2, self.cell_height)))
        self.fill(self.lighten(color), pygame.Rect((left, top + self.cell_height - 2), (self.cell_width, 2)))
        self.fill(self.lighten(color), pygame.Rect((left + self.cell_width - 2, top), (2, self.cell_height)))
    
    def lighten(self, color):
        return [int(x * 0.2) for x in color]

    def darken(self, color):
        return [min(255, int(x * 1.3)) for x in color]
    
    def render_waiting_screen(self):
        """
        For multiplayer games: We might be waiting for other players.
        """
        
        missing = self.game_model.listener.get_number_of_players_missing()
        plural_s = 's' if missing != 1 else ''
        text = "Waiting for %s more player%s ..." % (missing, plural_s)
        self.message_layover.render_message(text, fontsize=14, fade=False)        
    
    def render_game_over_screen(self):
        """
        Game's over. Draw a layover telling the player about his failure.
        """
        self.message_layover.render_message("GAME OVER", fontsize=48, fade=True)

    def render_winner_screen(self):
        """
        Player wins the multiplayer match!
        """
        self.message_layover.render_message("YOU WIN", fontsize=48, fade=True)
        
if __name__ == '__main__':
    from gamemodel import Game
    g = Game((10, 10))
    gw = GameWindow(g, (300, 600))
    assert gw.cell_width == 30, "Wrong cell width: %s" % gw.cell_width

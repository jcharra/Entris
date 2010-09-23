import pygame
import math
import logging
import os
import sys
import time
import random
import threading

from networking import ServerEventListener, create_new_game
from statuswindow import StatusWindow
from configscreen import ConfigScreen

from pygame.locals import K_LEFT, K_RIGHT, K_DOWN, K_a, K_s, K_ESCAPE
KEYMAP = {K_LEFT: 'WEST', K_RIGHT: 'EAST', K_DOWN: 'SOUTH'}
ROTATION_MAP = {K_a: 'COUNTERCLOCKWISE', K_s: 'CLOCKWISE'}

logger = logging.getLogger("gamewindow")
handler = logging.StreamHandler()
logger.setLevel(logging.DEBUG)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

class GameWindow(pygame.Surface):
    """
    The game window is the visualization of the game instance it is
    responsible for, and controls how keyboard input is propagated to it.
    
    TODO: The class also handles music and game sounds. Better put this in 
    a separate class maybe ...
    """
    
    def __init__(self, game, config):
        self.game = game
        dimensions = config['screen_size']
        self.cell_width = math.ceil(dimensions[0]/float(game.column_nr))
        self.cell_height = math.ceil(dimensions[1]/float(game.row_nr))

        self.dimensions = (self.cell_width * game.column_nr,
                           self.cell_height * game.row_nr)
        
        pygame.Surface.__init__(self, self.dimensions)

        # To get notified when a duck appears, add self to the list
        # of duck observers. For quacking sounds only.
        self.game.add_duck_observer(self)

        # A timer in milliseconds 
        self.clock = 0
        
        # The threshold (in milliseconds) indicating that the next step is due
        self.drop_interval = 500
        
        # Game over or interrupted
        self.finished = False
        
        # Since the downward acceleration by the player is meant to be "continuous"
        # (instead of having to press the "down" key again) we have to remember
        # if we're already in accelerated mode.
        self.downward_acceleration = False

        # Network stuff for playing online
        game_type = config['game_type']
        if game_type == ConfigScreen.SINGLE:       
            self.game.started = True
            self.listener = None
        else:
            # Game will be inactive until it gets the start
            # signal from the server.
            self.game.started = False
            
            if game_type == ConfigScreen.CREATE:
                game_id = create_new_game(size=config['game_info'])
                logger.info('Created game no. %s with size %s' % (game_id, config['game_info']))
            elif game_type == ConfigScreen.JOIN:
                game_id = config['game_info']
                logger.info('Joining game no. %s' % game_id)
            else:
                raise KeyError("Unknown game type: %s" % game_type)
            
            # Connect the game instance to the game server by adding 
            # a server listener to it. 
            self.listener = ServerEventListener(self.game,
                                                online_game_id=game_id)
            self.listener.listen()
     
        # In case of multiplayer games, this can become True.
        # Maybe I'll define a "winning state" for single player mode, too.
        self.game_won = False
     
        self.status_window = StatusWindow((200, self.get_height()), self.game)
    
        self.sound_directory = '../sound/'
        self.quack = pygame.mixer.Sound('%s/quack.ogg' % self.sound_directory)
        self.delete_sound = None
        self.play_random_music()
        
    def play_random_music(self):
        variations = [var for var in os.listdir(self.sound_directory) if var.startswith('var')]
        random_variation = "%s/%s" % (self.sound_directory, random.choice(variations))
        pygame.mixer.music.load(random_variation)
        pygame.mixer.music.play()
    
    def get_total_width(self):
        return self.get_width() + self.status_window.get_width()
          
    def handle_keyrelease(self, key):
        """
        User released a key - possibly the "down" key. So stop downward-
        accelerating the active piece.
        """
        
        self.downward_acceleration = False
        
    def handle_keypress(self, key):
        """
        Keypresses are mostly propagated to the game instance.
        """
        
        if key == K_ESCAPE:
            logger.error("Aborting game")
            self.finished = True
            if self.listener:
                self.listener.abort = True
            
        # Game may be waiting to start.
        # Don't propagate keyboard input in that case.
        if self.game.started:
            if key in KEYMAP:
                self.game.move_piece(KEYMAP[key])
                
                if key == K_DOWN:
                    self.downward_acceleration = True
                    
            elif key in ROTATION_MAP:
                self.game.rotate_piece(ROTATION_MAP[key])
        
    def update_view(self, screen, passed_time):
        """
        Render self and status window. Screen object to
        draw on is passed as an argument.
        
        passed_time is the time since the last call, which
        is just propagated to the render_game_window method.
        """
        
        self.render_game_window(passed_time)
        screen.blit(self, (0, 0))

        self.render_status_window()
        screen.blit(self.status_window, (self.get_width(), 0))        
        
    def render_game_window(self, passed_time):
        """
        Game may either be in state
        - over: display game over screen
        - won: display winner screen
        - in progress: display game
        """
        
        if self.game.gameover:
            if self.listener:
                self.listener.abort = True
            self.render_game_over_screen()
        elif self.game_won:
            self.render_winner_screen()
        else:            
            self.render_game(passed_time)

        # currently relevant for multiplayer games only
        if self.check_victory():
            self.game_won = True
            self.listener.abort = True
            
    def render_status_window(self):
        if self.listener:
            self.status_window.renderMultiPlayerScreen(self.listener.game_id, 
                                                       self.listener.players)
        else:
            self.status_window.renderSinglePlayerScreen()
    
    def check_victory(self):
        if not self.listener:
            # There may be a single player "victory" one day ... 
            # the conditions for that should be defined here.
            return False
        else:
            # we are alive, the game already started and
            # there is only one player left
            if (not self.listener.abort 
                and self.game.started 
                and len(self.listener.players) == 1):
                print "%s %s %s" % (self.listener, self.game.started, self.listener.players)
                return True                
    
    def duck_alert(self):
        """
        A duck hath appeared ... so quack!
        """
        self.quack.play()
    
    def render_game(self, passed_time):
        """
        Visualizes the game model w.r.t. the amount of time that passed.
        If the cumulative time has reached the threshold value stored as the
        update interval, tell the game to proceed first.
        """
        
        self.fill((0, 0, 0))
        
        if not self.game.started:
            return
        
        self.clock += passed_time
        threshold_reached, self.clock = divmod(self.clock, self.drop_interval)

        if self.downward_acceleration:  
            self.game.move_piece("SOUTH")
            
        if threshold_reached:
            self.game.proceed()
            complete_lines = self.game.find_complete_rows_indexes()
            if complete_lines:
                #self.delete_sound.play()
                self.game.delete_rows(complete_lines)
                
            self.drop_interval = max(50, 500 - self.game.level * 25)
        
        self.paint_cells()

    def paint_cells(self):
        """
        Paint the game grid, i.e. immobile pieces as well as the active one.
        """
        for idx, cell_value in enumerate(self.game.cells):
            if cell_value:
                # cell is filled with dead matter
                self.draw_cell(idx, cell_value)
            elif idx in self.game.moving_piece_indexes:
                # this cell is part of the moving piece
                self.draw_cell(idx, self.game.moving_piece.color)

    def draw_cell(self, index, color):
        """
        Draws a single cell in the grid with a given index (i.e. position)
        and the specified color.
        """
        
        top, left = divmod(index, self.game.column_nr)
        top *= self.cell_height
        left *= self.cell_width
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
    
    def render_game_over_screen(self):
        """
        Game's over. Draw a layover telling the player about his failure.
        """
        layover = pygame.Surface(self.dimensions)
        layover_bg = (50, 50, 50)
        layover.set_alpha(10)
        layover.fill(layover_bg)
        font = pygame.font.Font(None, 60)
        text = font.render('GAME OVER', True, (255, 0, 0), layover_bg)
        coords = self.dimensions[0]/2 - text.get_width()/2, self.dimensions[1]/2 - text.get_height()/2
        layover.blit(text, coords)
        self.blit(layover, (0, 0))

    def render_winner_screen(self):
        """
        Player wins the multiplayer match!
        """
        layover = pygame.Surface(self.dimensions)
        layover_bg = (50, 50, 50)
        layover.set_alpha(10)
        layover.fill(layover_bg)
        font = pygame.font.Font(None, 60)
        text = font.render('YOU WIN', True, (255, 0, 0), layover_bg)
        coords = self.dimensions[0]/2 - text.get_width()/2, self.dimensions[1]/2 - text.get_height()/2
        layover.blit(text, coords)
        self.blit(layover, (0, 0))

        
if __name__ == '__main__':
    from gamemodel import Game
    g = Game((10, 10))
    gw = GameWindow(g, (300, 600))
    assert gw.cell_width == 30, "Wrong cell width: %s" % gw.cell_width

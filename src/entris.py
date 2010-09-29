import pygame
from pygame.locals import *
pygame.init()

import sys
import os
import random

from gamemodel import Game
from gamewindow import GameWindow
from statuswindow import StatusWindow
from configscreen import ConfigScreen, GetInputScreen

CONFIG_SCREEN_DIMENSIONS = (400, 300)
        
def play_game(main_screen, config_screen):
    window = GameWindow(config_screen)
    
    # The true screen dimensions are available only after
    # the game window's dimensions have been "rounded" properly.
    true_x = window.get_total_width()
    true_y = window.get_height()
    
    pygame.display.set_mode((true_x, true_y))
    
    clock = pygame.time.Clock()
    
    while not window.finished:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                window.handle_keypress(event.key)
            elif event.type == pygame.KEYUP:
                window.handle_keyrelease(event.key)
        
        passed_time = clock.tick(30)
                
        window.update_view(main_screen, passed_time)
        pygame.display.update()

if __name__ == '__main__':
    config_screen = ConfigScreen(CONFIG_SCREEN_DIMENSIONS[0])
    
    while True:
        pygame.display.set_mode(CONFIG_SCREEN_DIMENSIONS)
        main_screen = pygame.display.get_surface()
        
        # show config screen until finished.
        config_screen.finished = False
        config_screen.show(main_screen)
        config = config_screen.as_dict()
        
        start_ok = True
        game_type = config['game_type']

        if game_type != ConfigScreen.SINGLE:
            # Player must provide some more input before being
            # allowed to start playing.
            start_ok = False
            
            if game_type == ConfigScreen.CREATE:
                number_input_screen = GetInputScreen(CONFIG_SCREEN_DIMENSIONS, 
                                           "Enter number of players", 
                                           input_type=GetInputScreen.NUMERIC,
                                           max_length=2,
                                           constraint=lambda x: int(x) in range(2, 11))
            elif game_type == ConfigScreen.JOIN:
                number_input_screen = GetInputScreen(CONFIG_SCREEN_DIMENSIONS, 
                                           "Enter game ID to join", 
                                           input_type=GetInputScreen.NUMERIC,
                                           max_length=5)
            else:
                raise KeyError("Unknown game type: %s" % game_type)
            
            # get user input
            number_input_screen.show(main_screen)
            
            user_input = number_input_screen.get_input()
            if user_input:
                config['game_info'] = user_input
                start_ok = True
            
        if start_ok:
            # Let's go ...
            play_game(main_screen, config)
        
        
        
        
        
        
        
        
        
        
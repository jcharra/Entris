import pygame
from pygame.locals import *
pygame.init()

import sys

from gamemodel import create_game
from gamewindow import GameWindow
from configscreen import ConfigScreen, GetInputScreen

CONFIG_SCREEN_DIMENSIONS = (400, 300)
        
def play_game(main_screen, config):
    game = create_game(config)
    game_window = GameWindow(config, game)
    
    pygame.display.set_mode((game_window.get_total_width(),
                             game_window.get_height()))
    
    clock = pygame.time.Clock()
    
    while not game.aborted:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                game.handle_keypress(event.key)
            elif event.type == pygame.KEYUP:
                game.handle_keyrelease(event.key)
        
        game_window.update_view(main_screen)
        pygame.display.update()
        
        passed_time = clock.tick(30)
        game.proceed(passed_time)
        

if __name__ == '__main__':
    config_screen = ConfigScreen(CONFIG_SCREEN_DIMENSIONS[0])
    pygame.display.set_caption('Entris')
    
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
            
            # Get player name
            player_name_screen = GetInputScreen(CONFIG_SCREEN_DIMENSIONS, 
                           "Enter your screen name", 
                           input_type=GetInputScreen.ALPHANUMERIC,
                           max_length=10)
            player_name_screen.show(main_screen)
            
            screen_name = player_name_screen.get_input() or ''
            config['screen_name'] = screen_name
            
            # Get additional information, depending on whether we
            # join or create the online game.    
            if game_type == ConfigScreen.CREATE:
                number_input_screen = GetInputScreen(CONFIG_SCREEN_DIMENSIONS, 
                                           "Enter number of players", 
                                           input_type=GetInputScreen.NUMERIC,
                                           max_length=2,
                                           constraint=lambda x: int(x) in range(2, 5))
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
        
        
        
        
        
        
        
        
        
        
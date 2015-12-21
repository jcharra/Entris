import pygame

pygame.init()

import sys

from gamemodel import create_game
from gamewindow import GameWindow

from config import GAME_WINDOW_DIMENSIONS, SCREEN_DIMENSIONS
from menu import build_menu

def main():
    main_screen = pygame.display.set_mode(SCREEN_DIMENSIONS)
    
    clock = pygame.time.Clock()
    
    start_window = build_menu(SCREEN_DIMENSIONS)
    currentConfigWindow = start_window

    # Outer infinite loop: Always return to config
    # when game is finished or aborted
    while True:
        # Inner infinite loop: Traverse config until finished
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                    
                if event.type == pygame.KEYDOWN:
                    currentConfigWindow.handle_keypress(event)
                elif event.type == pygame.KEYUP:
                    currentConfigWindow.handle_keyrelease(event)
            
            currentConfigWindow.render(main_screen)
            pygame.display.update()
            
            passed_time = clock.tick(30)
            currentConfigWindow.proceed(passed_time)
    
            if currentConfigWindow.finished:
                currentConfigWindow.finished = False
                next = currentConfigWindow.get_successor()
                if next:
                    currentConfigWindow = next
                else:
                    break
                
            elif currentConfigWindow.aborted:
                currentConfigWindow.aborted = False
                previous = currentConfigWindow.predecessor
                if previous:
                    currentConfigWindow = previous
                else:
                    sys.exit(0)
    
        config = start_window.collect_values_along_chosen_path()
        
        game = create_game(config)
        game_window = GameWindow(dimensions=GAME_WINDOW_DIMENSIONS, 
                                 game_model=game)
        
        while not game.aborted:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    sys.exit()
                    
                if event.type == pygame.KEYDOWN:
                    game.handle_keypress(event)
                elif event.type == pygame.KEYUP:
                    game.handle_keyrelease(event)
            
            game_window.update_view(main_screen)
            pygame.display.update()
            
            passed_time = clock.tick(30)
            game.proceed(passed_time)

if __name__ == '__main__':
    main()


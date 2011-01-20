
"""
Module for Entris-specific config
"""

from statewindows import GatewayWindow, InputWindow, MenuWindow, MenuItem

def build_config(dimensions):
    start = GatewayWindow(dimensions)
    start.add_items(MenuItem('game_type', (('single', 'Single player game'),
                                           ('create', 'Create online game'),
                                           ('join', 'Join online game'),)))
                   
    name = InputWindow(dimensions, 
                       'Enter player name:', 
                       'player_name', 
                       InputWindow.ALPHANUMERIC, 
                       10)
    
    single_game_config = MenuWindow(dimensions)
    single_game_config.add_items(MenuItem('game_size', (((20, 25), '20 x 25'),
                                                       ((25, 30), '25 x 30'))),
                                 MenuItem('duck_prob', ((0.0, '0%'),
                                                        (0.05, '5%'))))
    
    multi_game_config = MenuWindow(dimensions)
    multi_game_config.add_items(MenuItem('game_size', (((20, 25), '20 x 25'),
                                                       ((25, 30), '25 x 30'))),
                                MenuItem('player_number', ((2, "2 players"),
                                                           (3, "3 players"),
                                                           (4, "4 players"),
                                                           (5, "5 players"))),  
                                MenuItem('duck_prob', ((0.0, '0%'),
                                                        (0.05, '5%'))))
                   
    #lobby = None # still missing
                   
    start.set_successor(single_game_config, 0) 
    start.set_successor(multi_game_config, 1)
    #start.set_successor(lobby, 2)

    multi_game_config.set_successor(name)

    return start
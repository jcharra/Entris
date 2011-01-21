
"""
Module for Entris-specific config
"""

from statewindows import GatewayWindow, InputWindow, MenuWindow, MenuItem

GAME_TYPE_OPTIONS = (('single', 'Single player'),
                     ('create', 'Create online game'),
                     ('join', 'Join online game'))
    
GAME_SIZE_OPTIONS = [((x, y), "Grid size: %s x %s" % (x, y))
                      for (x, y) in ((20, 25), (25, 32), (30, 40))]

DUCK_PROB_OPTIONS = [(i/100.0, "Duck probability: %i%%" % i) 
                     for i in range(11)]

PLAYER_NUMBER_OPTIONS = [(i, "%i players" % i) 
                         for i in range(2, 6)]



def build_config(dimensions):
    start = GatewayWindow(dimensions, 'game_type')
                   
    name = InputWindow(dimensions, 
                       'Enter player name:', 
                       'screen_name', 
                       InputWindow.ALPHANUMERIC, 
                       10)
    
    single_game_config = MenuWindow(dimensions)
    single_game_config.add_items(MenuItem('game_size', 
                                          GAME_SIZE_OPTIONS),
                                 MenuItem('duck_prob', 
                                          DUCK_PROB_OPTIONS))
    
    create_game_config = MenuWindow(dimensions)
    create_game_config.add_items(MenuItem('game_size', 
                                          GAME_SIZE_OPTIONS),
                                 MenuItem('player_number', 
                                          PLAYER_NUMBER_OPTIONS),  
                                 MenuItem('duck_prob', 
                                          DUCK_PROB_OPTIONS))
                   
    #lobby = None # still missing
                   
    start.add_item_with_successor('single', 
                                  'Single player game', 
                                  single_game_config) 
    start.add_item_with_successor('create', 
                                  'Create online game', 
                                  create_game_config)
    #start.set_successor(lobby, 2)

    create_game_config.set_successor(name)

    return start
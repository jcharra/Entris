
"""
Module for Entris-specific config
"""

from statewindows import GatewayWindow, InputWindow, MenuWindow, MenuItem

GAME_TYPE_OPTIONS = (('single', 'Single player'),
                     ('create', 'Create online game'),
                     ('join', 'Join online game'))
    
GAME_SIZE_OPTIONS = [((x, y), "%s x %s" % (x, y))
                      for (x, y) in ((20, 25), (25, 32), (30, 40))]
DUCK_PROB_OPTIONS = [(i/100.0, "%i" % i) 
                     for i in range(11)]
PLAYER_NUMBER_OPTIONS = [(i, "%i players" % i) 
                         for i in range(2, 6)]



def build_config(dimensions):
    start = GatewayWindow(dimensions, 'game_type', GAME_TYPE_OPTIONS)
                   
    name = InputWindow(dimensions, 
                       'Enter player name:', 
                       'player_name', 
                       InputWindow.ALPHANUMERIC, 
                       10)
    
    single_game_config = MenuWindow(dimensions)
    single_game_config.add_items(MenuItem('Game size', 
                                          'game_size', 
                                          GAME_SIZE_OPTIONS),
                                 MenuItem('Duck probability', 
                                          'duck_prob', 
                                          DUCK_PROB_OPTIONS))
    
    multi_game_config = MenuWindow(dimensions)
    multi_game_config.add_items(MenuItem('Game size', 
                                         'game_size', 
                                         GAME_SIZE_OPTIONS),
                                MenuItem('Players', 
                                         'player_number', 
                                         PLAYER_NUMBER_OPTIONS),  
                                MenuItem('Duck probability', 
                                         'duck_prob', 
                                         DUCK_PROB_OPTIONS))
                   
    #lobby = None # still missing
                   
    start.set_successor(single_game_config, 0) 
    start.set_successor(multi_game_config, 1)
    #start.set_successor(lobby, 2)

    multi_game_config.set_successor(name)

    return start
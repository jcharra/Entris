
from config import GAME_SIZE_OPTIONS, DUCK_PROB_OPTIONS, PLAYER_NUMBER_OPTIONS
from statewindows import GatewayWindow, InputWindow, MenuWindow, MenuItem
from lobby import Lobby

def build_menu(dimensions):
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
                   
    lobby = Lobby()
                   
    start.add_item_with_successor('single', 
                                  'Single player game', 
                                  single_game_config) 
    start.add_item_with_successor('create', 
                                  'Create online game', 
                                  create_game_config)
    start.add_item_with_successor('join', 'Join online game', lobby)

    create_game_config.set_successor(name)

    return start
from config import GAME_DIMENSIONS_OPTIONS, DUCK_PROB_OPTIONS, PLAYER_NUMBER_OPTIONS
from statewindows import GatewayWindow, InputWindow, MenuWindow, MenuItem
from lobby import Lobby


def build_menu(dimensions):
    name_input_menu = InputWindow(dimensions,
                                  'Enter player name:',
                                  'screen_name',
                                  InputWindow.ALPHANUMERIC,
                                  10)

    server_input_menu = InputWindow(dimensions,
                                    'Enter server address and port (host:port)',
                                    'server_name',
                                    InputWindow.HOST,
                                    25)

    game_type_selection = GatewayWindow(dimensions, 'game_type')

    single_game_config = MenuWindow(dimensions)
    single_game_config.add_items(MenuItem('dimensions',
                                          GAME_DIMENSIONS_OPTIONS),
                                 MenuItem('duck_prob',
                                          DUCK_PROB_OPTIONS))

    create_game_config = MenuWindow(dimensions)
    create_game_config.add_items(MenuItem('dimensions',
                                          GAME_DIMENSIONS_OPTIONS),
                                 MenuItem('size',
                                          PLAYER_NUMBER_OPTIONS),
                                 MenuItem('duck_prob',
                                          DUCK_PROB_OPTIONS))

    lobby = Lobby()

    # Now build a successor/predecessor tree from the constructed menus

    name_input_menu.set_successor(game_type_selection)
    game_type_selection.add_item_with_successor('single',
                                                'Single player game',
                                                single_game_config)
    game_type_selection.add_item_with_successor('create',
                                                'Create online game',
                                                create_game_config)
    game_type_selection.add_item_with_successor('join', 'Join online game', lobby)

    create_game_config.set_successor(server_input_menu)

    return name_input_menu

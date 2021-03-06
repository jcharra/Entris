import sys

import pygame

import math
from part import random_part_generator


def compress(game):
    """
    Builds a compressed version of a game instance
    """
    cells = "".join(["1" if (c or idx in game.moving_piece_indexes) 
                     else "0" 
                     for idx, c in enumerate(game.cells)])
    return str(game.column_nr) + "," + cells

def decompress(compressed):
    """
    Builds a two-dimensional boolean array from a compressed
    string representing a game.
    """
    
    parts = compressed.split(",")
    
    if len(parts) != 2:
        # Probably still empty ... ignore it
        return None
    
    row_length_str, data = int(parts[0]), parts[1]
    row_length = int(row_length_str)
    
    number_of_rows = len(data)/row_length
    
    bin_array = []
    for idx in range(int(number_of_rows)):
        bin_array.append([int(x) for x in data[idx*row_length:(idx+1)*row_length]])
    
    return bin_array

class GameMonitor(pygame.Surface):
    """
    Class to render a micro view of a game given
    in an encoded format.
    """

    def __init__(self, dimensions):
        self.dimensions = dimensions
        pygame.Surface.__init__(self, self.dimensions)
        self.font = pygame.font.Font('jack_type.ttf', 14)
        self.big_font = pygame.font.Font('jack_type.ttf', 36)
        
    def render_game(self, compressed_game, player_name, player_alive):
        """
        Expects a string representing a game in compressed
        format, as resulting from the 'compress' function above.
        """

        self.fill((0, 0, 0))
        
        if compressed_game:
            game_as_array = decompress(compressed_game)
            nr_columns, nr_rows = len(game_as_array[0]), len(game_as_array)
            pixel_width = self.get_width()/float(nr_columns)
            pixel_height = self.get_height()/float(nr_rows)
             
            for row_index, row in enumerate(game_as_array):
                for index, entry in enumerate(row):
                    if entry:
                        x_offset = index * pixel_width
                        y_offset = row_index * pixel_height
                        x_width = math.ceil((index+1) * pixel_width - x_offset)
                        y_height = math.ceil((row_index+1) * pixel_height - y_offset)
                                    
                        self.fill((100, 100, 255), 
                                  pygame.Rect(x_offset, y_offset, x_width, y_height)) 

        if player_name:
            color = player_alive and (0, 255, 0) or (100, 100, 100) 
            name_img = self.font.render(player_name, 1, color)
            self.blit(name_img, (5, 5))
        else:
            question_mark_img = self.big_font.render("?", 1, (200, 0, 0))
            qm_pos = question_mark_img.get_rect()
            qm_pos.centerx = self.get_width() / 2
            qm_pos.centery = self.get_height() / 2
            self.blit(question_mark_img, qm_pos)
            
if __name__ == '__main__':
    from gamemodel import Game
    
    config = {'game_size': (10, 10),
              'duck_prob': 0.1}
    game = Game(config['game_size'], 
                random_part_generator(config['duck_prob']))
    
    game.cells = [0] * 10
    game.cells += [(1, 1, 1)] * 9
    game.cells += [0]
    compressed = compress(game)
    assert compressed == "10,00000000001111111110", "Compressed repr corrupted: %s" % compressed
    
    decomp = decompress("10,00000000001111111110")
    assert decomp == [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [1, 1, 1, 1, 1, 1, 1, 1, 1, 0]], "Bad decompression: %s" % decomp
    
    # Test a bigger game ...
    game.cells = [0] * 70
    game.cells += [(1, 1, 1)] * 8
    game.cells += [0, 0]
    game.cells += [(1, 1, 1)] * 9
    game.cells += [0]
    game.cells += [(1, 1, 1)] * 10
    compressed = compress(game)
    
    pygame.init()
    moni = GameMonitor((100, 100))
    pygame.display.set_mode((100, 100))
    main_screen = pygame.display.get_surface()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                sys.exit()
                
        moni.render_game(compressed, 'eric', True)
        main_screen.blit(moni, (0, 0))
        pygame.display.update()
        
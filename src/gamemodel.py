
import random
import logging
from collections import deque
from part import Part, random_part_generator, DUCK_INDICES

logger = logging.getLogger("gamemodel")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

class Game(object):

    def __init__(self, dimensions, duck_probability=0):
        self.column_nr, self.row_nr = self.dimensions = dimensions
        self.cells = [0 for _ in range(self.column_nr) for _ in range(self.row_nr)]
        self.moving_piece = None
        
        self.score = 0
        self.level = 0
        self.next_level_threshold = 20000
        self.gameover = False
        
        # Only relevant if it's a network game
        # waiting for other players. Set to True
        # or False by the controlling GameWindow
        # instance (and possibly by the ServerEventListener
        # instance in case of network games).
        self.started = False
        
        self.init_direction_map()

        self.setup_part_probabilities(duck_probability)
        self.init_piece_queue()
        
        self.duck_observers = []
        self.line_observers = []
        
        # For multiplayer mode only:
        # Penalties can be received from other players
        self.penalties = deque()
        
        logger.debug("Initialized game")
    
    def init_direction_map(self):
        """
        Returns a mapping of the four basic directions
        N, E, S, W to corresponding differences in means
        of grid indexes.
        """
        
        self.direction_map = dict(NORTH = -self.column_nr,
                                  EAST  = 1,
                                  SOUTH = self.column_nr,
                                  WEST  = -1)
    
    def init_piece_queue(self):
        self.piece_queue = deque([self.part_generator.next() for _ in range(10)])
        
    def proceed(self):
        """
        Takes one step in time.
        
        If there is a piece currently moving, move it if possible.
        Otherwise create a new one on top of the grid. 
        """
        
        if self.moving_piece:
            moved = self.move_piece("SOUTH")
            if not moved:
                # Cannot move downward any further
                # => turn the moving piece into lifeless concrete
                for idx in self.moving_piece.get_indexes():
                    self.cells[idx] = self.moving_piece.color
                self.moving_piece = None
        else:
            
            # Time to insert penalty lines, if any
            if self.penalties:
                self.insert_penalties()
            
            # create and insert a new piece
            next_piece = self.get_next_piece()
            self.insert_new_moving_piece(next_piece)
            
            # If there is any overlap with existing pieces, we're screwed
            if any([self.cells[i] for i in self.moving_piece.get_indexes()]):
                self.gameover = True
            
        
    def rotate_piece(self, rotation_key, steps=1):
        """
        Tries to rotate the current piece
        """

        if (not self.moving_piece 
            or not self.rotation_legal(steps, rotation_key == "CLOCKWISE")):
            return False

        self.moving_piece.rotate(steps, rotation_key == "CLOCKWISE")
        
    def rotation_legal(self, steps, clockwise):
        """
        Returns whether rotating the active piece <steps> steps in the
        direction given by <clockwise> is possible.
        """
        
        # 1. Check illegal overlap
        rotated_indexes = self.moving_piece.get_indexes(added_rotation=steps)
        try:
            if any([self.cells[i] for i in rotated_indexes]):
                return False
        except IndexError:
            return False
        
        # 2. Check rotation across the vertical borders.
        # This may look a little strange ... the idea is that if, after the 
        # attempted rotation, there would be squares of the moving piece both 
        # in the first and the last column, then the rotation must be illegal, 
        # since it apparently crosses the vertical borders.
        x_coords = [x % self.column_nr for x in rotated_indexes]
        
        # See explanation above: If the rotation crossed a vertical border, then
        # the minimum and maximum column indexes will be too far apart for a 
        # coherent piece. The 9 is a little too arbitrary here ... should be 
        # "less or equal the maximum piece width".
        return max(x_coords) - min(x_coords) < 9
        
    def move_piece(self, direction_key):
        """
        Tries to move the active piece in the given direction.
        Returns True/False accordingly.
        
        direction_key must be in ("NORTH", "EAST", "SOUTH", "WEST")
        """
        
        if not self.moving_piece:
            return False
        
        assert direction_key in ("NORTH", "EAST", "SOUTH", "WEST")
        direction_delta = self.direction_map[direction_key]
        if not self.move_legal(direction_delta):
            return False
        
        self.moving_piece.position_index += direction_delta
        
        return True
        
    def move_legal(self, direction_delta):
        """
        Check the validity of a move that consists of increasing 
        the active piece's cell indexes by the given direction_delta.
        
        Returns True/False
        """
        try:
            # Check for blocked cells
            if any([self.cells[idx + direction_delta] for idx in self.moving_piece.get_indexes()]):
                return False
            
            # Check for border-crossing of horizontal moves
            if direction_delta in (1, -1):
                active_part_indexes = self.moving_piece.get_indexes()
                if ([(idx + direction_delta)/self.column_nr 
                     for idx in active_part_indexes]
                    != [idx/self.column_nr 
                        for idx in active_part_indexes]):
                    return False
        except IndexError:
            return False
            
        return True
        
    def get_row_contents(self, n):
        """
        Returns the values of the nth row in the grid
        """
        return self.cells[n*self.column_nr:(n+1)*self.column_nr]

    def find_complete_rows_indexes(self):
        """
        Returns a list containing the indexes of all completed rows.
        E.g. if the grid has 20 rows and the bottom two rows are complete, 
        return [18, 19].
        """
        removable_rows = []
        for row_idx in range(self.row_nr):
            if all(self.get_row_contents(row_idx)):
                removable_rows.append(row_idx)
        return removable_rows

    def delete_rows(self, row_indexes):
        """
        Deletes the indicated rows from the grid and preprends a 
        corresponding number of empty lines.
        """
        
        self.cells = [cell for i, cell in enumerate(self.cells) 
                      if i/self.column_nr not in row_indexes]

        for _ in row_indexes:
            self.cells = [0 for _ in range(self.column_nr)] + self.cells
            
        self.add_score(len(row_indexes))
            
        for obs in self.line_observers:
            obs.notify(number_of_lines=len(row_indexes))

    def add_score(self, number_of_lines_cleared):
        """
        Increases the score. This ought to be refined a little.
        """
        score_gain = (number_of_lines_cleared * 35) ** 2
        self.score += score_gain
        
        if self.score >= self.next_level_threshold:
            self.next_level_threshold += 50000
            self.level += 1
            logger.warn("Next level reached")

    @property
    def moving_piece_indexes(self):
        return self.moving_piece and self.moving_piece.get_indexes() or []

    def setup_part_probabilities(self, duck_prob):
        self.part_generator = random_part_generator(duck_prob)

    def get_next_piece(self):
        next = self.piece_queue.popleft()
        self.piece_queue.append(self.part_generator.next())
        return next
    
    def insert_new_moving_piece(self, piece):
        if piece == DUCK_INDICES:
            for obs in self.duck_observers:
                obs.duck_alert()

        piece = Part(piece, self.column_nr)
        piece.position_index = self.column_nr/2 - 1
        piece.rotate(random.randint(0, 3), clockwise=True)
    
        self.moving_piece = piece
    
    def regurgitate(self, number_of_lines):
        """
        Puts a regurgitation event into the queue
        """
        
        self.penalties.append(number_of_lines)
        logger.info("Penalties increased to %s" % self.penalties)
        
    def insert_penalties(self):
        number_of_lines = self.penalties.popleft()
        
        # delete the topmost n rows
        del self.cells[:self.column_nr * number_of_lines]
        
        # for each penalty, insert a row at the bottom having 
        # a two-squared random gap 
        for _ in range(number_of_lines):
            penalty_line = [(100, 100, 100) for _ in range(self.column_nr)]
            gap_index = random.randint(0, self.column_nr - 1)
            penalty_line[gap_index:gap_index+1] = 0, 0
            self.cells.extend(penalty_line * number_of_lines)
        
    def add_duck_observer(self, observer):
        self.duck_observers.append(observer)

    def add_line_observer(self, observer):
        self.line_observers.append(observer)
    
    def __repr__(self):
        rows = []
        for i in range(self.row_nr):
            rows.append(",".join([str(self.cells[j]) 
                                  for j in range(i * self.column_nr, (i + 1) * self.column_nr)]))
        return "\n".join(rows)
    
if __name__ == '__main__':
    config = {'game_size': (10, 10),
              'duck_prob': 0.1}
    game = Game(config)
    assert game.cells == [0] * 100
    # proceed until piece arrives at bottom
    while not any([game.cells]):
        game.proceed()
    # check if sth arrived at the bottom row
    assert any([game.cells[-game.column_nr:]])
    
    # Fill the cells to check deletion.
    # Row indexes 7 and 8 are filled, last line almost filled.
    game.cells = [0] * 70
    game.cells += [(1, 1, 1)] * 29
    game.cells += [0]
    indexes = game.find_complete_rows_indexes()
    assert indexes == [7, 8], 'find_complete_rows_indexes failed'
    game.delete_rows(indexes)
    assert game.cells == [0] * 90 + [(1, 1, 1)] * 9 + [0], "Deletion incorrect: \n%s" % game
    
    assert len(game.piece_queue) == 10, "Piece queue not initialized properly"
    old_queue = list(game.piece_queue)
    game.get_next_piece()
    assert old_queue[1:] == list(game.piece_queue)[:-1], "%s is not the predecessor of %s" % (old_queue, game.piece_queue)
    
    game.cells = [0] * 100
    game.penalties = deque([2])
    game.insert_penalties()
    cells_afterwards_should_be = [0] * 80 + [(100, 100, 100), 0] * 10
    assert game.cells == cells_afterwards_should_be, "\n%s \nvs.\n%s" % (game.cells, cells_afterwards_should_be)
    
    
    
    
    
    
            
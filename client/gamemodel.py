
import logging
import random

from collections import deque
from part import Part, DUCK_INDICES, random_part_generator, get_part_for_index
from events import LinesDeletedEvent, QuackEvent
from networking import ServerEventListener, create_new_game, ConnectionFailed

logger = logging.getLogger("gamemodel")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

from pygame.locals import K_LEFT, K_RIGHT, K_DOWN, K_a, K_s, K_ESCAPE
KEYMAP = {K_LEFT: 'WEST', K_RIGHT: 'EAST', K_DOWN: 'SOUTH'}
ROTATION_MAP = {K_a: 'COUNTERCLOCKWISE', K_s: 'CLOCKWISE'}

def create_game(config):
    """
    Factory method to create a game based 
    on the parameters in the config.
    """
    
    # We need to pass a part generator with the appropriate probabilities.        
    # as an argument.
    part_generator = random_part_generator(config['duck_prob'])
    game_type = config['game_type']
    game_dimensions = config['game_size']
    
    if game_type == 'single':
        game = SingleplayerGame(game_dimensions, part_generator)
        game.started = True
        game.listener = None
    else:
        if game_type == 'create':
            game_id = create_new_game(size=config['player_number'],
                                      duck_probability=config['duck_prob'])
        elif game_type == 'join':
            game_id = config['game_id']
        else:
            raise KeyError("Unknown game type: %s" % game_type)

        game = MultiplayerGame(game_dimensions, part_generator)

        # Game will be inactive until it gets the start
        # signal from the server.
        game.started = False
        
        try:
            # Connect the game instance to the game server by adding 
            # a server listener to it. 
            game.listener = ServerEventListener(game,
                                                online_game_id=game_id,
                                                screen_name=config['screen_name'])
            game.listener.listen()
        except ConnectionFailed, msg:
            # This game must be immediately aborted.
            # Apparently it doesn't exist.
            game.aborted = True

    return game

class Game(object):

    def __init__(self, dimensions, part_generator):
        self.column_nr, self.row_nr = self.dimensions = dimensions
        
        # Initialize all cells to zero (=not occupied)
        self.cells = [0 for _ in range(self.column_nr) for _ in range(self.row_nr)]
        
        # The active piece for the player to control
        self.moving_piece = None
        
        # Game is lost
        self.gameover = False
        # Game is won (probably for multiplayer only)
        self.victorious = False
        # Game is aborted
        self.aborted = False
        
        # Initially the game waits for a start signal
        # from a controlling object (either the GameWindow
        # instance owning the game, or - for network games
        # the ServerEventListener instance)
        self.started = False
        
        self.init_direction_map()

        # A generator for yielding an inexhaustible 
        # supply of new game parts
        self.part_generator = part_generator
        self.init_piece_queue()

        # Observers will watch out for ducks appearing,
        # lines being deleted etc. 
        self.observers = []
        
        # This represents the dropping speed of the active
        # piece, i.e. the time in ms between each step.
        self.drop_interval = 500
        
        # Since the downward acceleration by the player is meant to be "continuous"
        # (instead of having to press the "down" key again) we have to remember
        # if we're already in accelerated mode.
        self.downward_accelerated = False
        
        # The game model keeps track of the time that has passed
        self.clock = 0
        
    def init_direction_map(self):
        """
        Initializes the mapping of the four basic directions
        N, E, S, W to corresponding differences in means
        of grid indexes.
        """        
        self.direction_map = dict(NORTH = -self.column_nr,
                                  EAST  = 1,
                                  SOUTH = self.column_nr,
                                  WEST  = -1)
    
    def init_piece_queue(self):
        """
        This method can probably be removed after some refactoring
        """
        self.piece_queue = deque([self.part_generator.next() for _ in range(10)])
    
    def handle_keypress(self, key):
        if key == K_ESCAPE:
            self.tear_down()
            
        # Game may be waiting to start.
        # Don't propagate keyboard input in that case.
        if not self.started:
            return
        
        if key in KEYMAP:
            self.move_piece(KEYMAP[key])
            
            if key == K_DOWN:
                self.downward_accelerated = True
                
        elif key in ROTATION_MAP:
            self.rotate_piece(ROTATION_MAP[key])

    def handle_keyrelease(self, key):
        """
        Currently only the release of the "down" key is relevant,
        as that will toggle the downward acceleration.
        """
        
        if key == K_DOWN:
            self.downward_accelerated = False
      
    def tear_down(self):
        self.aborted = True
    
    def handle_game_over(self):
        self.gameover = True
   
    def proceed(self, passed_time):
        """
        Lets the given amount of time 'pass'. If the accumulated time
        is greater than the drop interval (=the game speed), reset the 
        clock and move the active piece downwards.
        """
        
        if not self.started or self.gameover or self.victorious:
            return
        
        self.clock += passed_time
        threshold_reached, self.clock = divmod(self.clock, self.drop_interval)

        if self.downward_accelerated:  
            self.move_piece("SOUTH")
            
        if threshold_reached:
            self.take_one_step()
            complete_lines = self.find_complete_rows_indexes()
            if complete_lines:
                self.delete_rows(complete_lines)
            
            acceleration = getattr(self, 'level', 0)
            self.drop_interval = max(50, 500 - acceleration * 25)

        self.check_victory()
        
    def take_one_step(self):
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
            # create and insert a new piece
            next_piece = self.get_next_piece()
            self.insert_new_moving_piece(next_piece)
            
            # If there is any overlap with existing pieces, we're screwed
            if any([self.cells[i] for i in self.moving_piece.get_indexes()]):
                self.handle_game_over()
            
    def check_victory(self):
        return False
       
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
            
        self.after_row_deletion(len(row_indexes))
        
    def after_row_deletion(self, number_of_rows):
        """
        Propagates the number of rows to registered line observers.
        """
        for obs in self.observers:
            obs.notify(LinesDeletedEvent(number_of_rows))

    @property
    def moving_piece_indexes(self):
        return self.moving_piece and self.moving_piece.get_indexes() or []

    def get_next_piece(self):
        next = self.piece_queue.popleft()
        self.piece_queue.append(self.part_generator.next())
        return next
    
    def insert_new_moving_piece(self, template):
        if template == DUCK_INDICES:
            for obs in self.observers:
                obs.notify(QuackEvent())

        part = Part(template, self.column_nr)
        part.position_index = self.column_nr/2 - 1
        part.rotate(random.randint(0, 3), clockwise=True)
    
        self.moving_piece = part
            
    def add_observer(self, observer):
        self.observers.append(observer)

    def __repr__(self):
        rows = []
        for i in range(self.row_nr):
            rows.append(",".join([str(self.cells[j]) 
                                  for j in range(i * self.column_nr, (i + 1) * self.column_nr)]))
        return "\n".join(rows)
    
    
class MultiplayerGame(Game):
    def __init__(self, dimensions, duck_probability=0):
        Game.__init__(self, dimensions, duck_probability)

        # Penalties can be received from other players
        self.penalties = deque()

    def proceed(self, passed_time):
        if not self.moving_piece and self.penalties:
            # Time to insert penalty lines, if any
            self.insert_penalties()

        Game.proceed(self, passed_time)
    
    def check_victory(self):
        # we are alive, the game already started and
        # there is only one player left => victory, dude! :)
        self.victorious = (not self.aborted
                           and not self.gameover
                           and self.started 
                           and len(self.listener.players) == 1)
        
        return self.victorious    
    
    def init_piece_queue(self):
        """
        Get new pieces from the server
        """
        self.piece_queue = deque()#self.listener.get_next_parts()
    
    def get_next_piece(self):
        if len(self.piece_queue) < 10:
            next_parts = [get_part_for_index(idx)
                          for idx in self.listener.get_next_parts()]
            self.piece_queue.extend(next_parts)
        return self.piece_queue.popleft()
                       
    def regurgitate(self, number_of_lines):
        """
        Puts a regurgitation event into the queue
        """
        self.penalties.append(number_of_lines)
        logger.info("Penalties increased to %s" % self.penalties)
        
    def insert_penalties(self):
        number_of_lines = self.penalties.popleft()
        
        penalty_is_fatal = any(self.cells[:self.column_nr * number_of_lines])
        
        # delete the topmost n rows
        del self.cells[:self.column_nr * number_of_lines]
        
        # for each penalty, insert a row at the bottom having 
        # a two-squared random gap 
        for _ in range(number_of_lines):
            penalty_line = [(100, 100, 100) for _ in range(self.column_nr)]
            gap_index = random.randint(0, self.column_nr - 1)
            penalty_line[gap_index:gap_index+1] = 0, 0
            self.cells.extend(penalty_line * number_of_lines)
    
        if penalty_is_fatal:
            # That was too much to swallow ... we're screwed
            self.handle_game_over()
        
class SingleplayerGame(Game):
    def __init__(self, dimensions, duck_probability=0):
        Game.__init__(self, dimensions, duck_probability)

        self.score = 0
        self.level = 0
        self.next_level_threshold = 20000

    def after_row_deletion(self, number_of_rows):
        self.add_score(number_of_rows)
        Game.after_row_deletion(self, number_of_rows)

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

    
if __name__ == '__main__':
    config = {'game_size': (10, 10),
              'duck_prob': 0.1}
    game = Game(config['game_size'], 
                random_part_generator(config['duck_prob']))
    
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
    
    
    
    
    
    
    
    
            

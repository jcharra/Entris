
import time
from collections import deque
import random
import logging
import itertools
import json 

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

######################################################
# Global dictionary mapping game_ids to Game instances
games = {}

logger = logging.getLogger('Server')

class GameFull(Exception):
    pass

def next_id(not_available):
    """
    Returns an unassigned id. not_available is a dictionary
    of IDs that are already assigned.
    """
    pid = random.randint(1000, 100000)
    while str(pid) in not_available:
        pid = random.randint(1000, 100000)
    return str(pid)

def random_part_index_generator(duck_probability=0.1):
    """
    Generator to produce an infinite sequence of
    indexes, ranging from 0 to 7.
    0 is returned with the probability specified by the
    argument 'duck_probability', the other parts share
    the remaining probability evenly.
    """
    
    while True:
        rand = random.random()
        if rand <= duck_probability:
            yield 0
        else:
            yield random.randint(1, 7)
  
def json_error(msg):
    return json.dumps({'error': msg})

def json_info(msg):
    return json.dumps({'info': msg})
   
def json_dumps(obj):
    return json.dumps(obj, separators=(',', ':'))
   
class Game():
    def __init__(self, config):
        self.game_id = config['game_id']
        self.size = max(min(config['size'], 6), 2)
        self.dimensions = config['dimensions']
        self.duck_prob = config['duck_prob']
        
        self.seconds_timeout_to_unregister = 5
        
        # A mapping from player ids to numbers indicating
        # pending penalty lines
        self.player_penalties = {}
        
        # A mapping from player ids to screen names
        self.screen_names = {}
        
        # A mapping from player ids to timestamps 
        # representing their last GET request for punishment.
        self.last_get_timestamp = {}
        
        # A mapping from the game's player ids
        # to snapshots of their game states,
        # in compressed format
        self.game_snapshot = {}
        
        # The 'global' part index generator that all players
        # receive their parts from.
        self.part_index_generator = random_part_index_generator(self.duck_prob)
        
        # A mapping from player id to part index generator.
        self.part_generator_for_player_id = {}
        
        # Game starts when all players have logged on
        self.started = False
        
        self.creation_timestamp = time.time()
    
    @property
    def free_slots(self):
        return self.size - len(self.screen_names)
    
    def as_short_dict(self):
        return {'game_id': self.game_id,
                'screen_names': self.screen_names,
                'size': self.size,
                'dimensions': self.dimensions,
                'duck_prob': self.duck_prob,
                'started': self.started,
                'free_slots': self.free_slots,
                'timestamp': self.creation_timestamp}
    
    def as_long_dict(self):
        d = self.as_short_dict()
        d['snapshots'] = self.game_snapshot
        return d
    
    def add_player(self, screen_name):
        if self.started or len(self.player_penalties) >= self.size:
            raise GameFull("Joining no longer possible (Game started: %s)" % self.started)
            
        player_id = next_id(self.player_penalties)
        self.player_penalties[player_id] = deque()
        
        # Use default if screen name is missing
        self.screen_names[player_id] = (self.adjust_name(screen_name) 
                                        if screen_name else "player%s" % player_id)
        self.game_snapshot[player_id] = ''        
        
        if self.is_full():
            for pid in self.player_penalties:
                self.last_get_timestamp[pid] = time.time()
                
            # Now produce as many identical generators from the 
            # 'master' as there are players in the game.
            spawned_part_generators = itertools.tee(self.part_index_generator, self.size)
            
            # Grab a part generator for each player
            self.part_generator_for_player_id = dict(zip(self.player_penalties.keys(),
                                                         spawned_part_generators))
                
            self.started = True
            
        #print "Added player %s to game %s" % (player_id, self.game_id)
        return player_id

    def delete_player(self, player_id):
        try:
            del self.player_penalties[player_id]
            del self.screen_names[player_id]
        except KeyError:
            logger.info("Player %s cannot be deleted (not found)" % player_id)
        
    def adjust_name(self, desired_name):
        """
        If a player attempts to have a screen name that already
        exists, give him an additional number in braces, like
        "eric(2)", "eric(3)" etc.
        """
        
        not_available = self.screen_names.values()
        
        if desired_name not in not_available:
            return desired_name
        
        c = 2
        while "%s(%s)" % (desired_name, c) in not_available:
            c += 1
        return "%s(%s)" % (desired_name, c)

    def is_full(self):
        return len(self.player_penalties) == self.size

    def is_alive(self):
        return len(self.player_penalties) > 1
    
    def store_snapshot(self, player_id, snapshot):
        logger.info("Store %s for player id %s" % (snapshot, player_id))
        self.game_snapshot[player_id] = snapshot
    
    def get_snapshots(self):
        items = ["%s:%s" % (pid, snapshot) 
                 for pid, snapshot in self.game_snapshot.items()]
        return ";".join(items)
    
    def get_names(self):
        items = ["%s:%s" % (pid, name) 
                 for pid, name in self.screen_names.items()
                 if pid in self.player_penalties]
        return ",".join(items)
    
    def get_parts(self, player_id):
        """
        Returns the next 10 parts for the requesting player
        """
        part_gen = self.part_generator_for_player_id[player_id]
        return [part_gen.next() for _ in range(10)]
            
    def get_penalties(self, player_id):
        stamp = time.time()
        
        self.kick_timed_out_players(stamp)
                
        if player_id not in self.player_penalties:
            return 0
        
        self.last_get_timestamp[player_id] = stamp
        
        return self.player_penalties[player_id]

    def kick_timed_out_players(self, stamp):
        kickable_players = []

        # find timed out players
        for player, last_stamp in self.last_get_timestamp.items():
            if stamp - last_stamp > self.seconds_timeout_to_unregister:
                kickable_players.append(player)
        
        # remove them both from the penalty and
        # timestamp dictionaries
        for kickable in kickable_players:
            del self.last_get_timestamp[kickable]
            try:
                del self.player_penalties[kickable]
            except KeyError, err:
                pass
                    

GAME_TIMEOUT_IN_SECONDS = 180
def delete_finished_and_empty_games():
    removable = []
    now = time.time()
    
    for game_id, game in games.items():
        if not game.is_alive():
            # Started but no more players in it => remove it
            removable.append(game_id)

        # Not started but too old => remove it            
        if not game.started and now - game.creation_timestamp > GAME_TIMEOUT_IN_SECONDS:
            removable.append(game_id)
            
    for game_id in removable:
        del games[game_id]

MAX_GAME_NUMBER = 100
class NewGameRequest(webapp.RequestHandler):
    def post(self):
        
        # To avoid a separate job periodically deleting old (i.e. finished)
        # games, do the cleaning up here.
        delete_finished_and_empty_games()
        
        self.response.headers['Content-Type'] = 'application/json'
        
        if len(games) >= MAX_GAME_NUMBER:
            self.response.out.write(json_error('Server full!'))
            return
            
        size = int(self.request.get('size', default_value="2"))
        duck_prob = float(self.request.get('duck_prob', default_value="0.01"))
        dimensions_str = self.request.get('dimensions', default_value="20x25")
        dimensions = [int(x) for x in dimensions_str.split('x')]
        game_id = next_id(games)
        
        game_config = dict(game_id=game_id,
                           size=size,
                           dimensions=dimensions,
                           duck_prob=duck_prob)
        
        game = Game(game_config)
        games[game_id] = game
        
        self.response.out.write(json_dumps(game_config))

class ListGamesRequest(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'
        games_list = [game.as_short_dict() for game in games.values()]
        games_json = json_dumps(games_list)
        self.response.out.write(games_json)

class RegistrationRequest(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'
        game_id = self.request.get('game_id')
        
        # screen name may not be given
        screen_name = self.request.get('screen_name', None)
        
        game = games[game_id]
        try:
            # fetch a player id for the newbie
            pid = game.add_player(screen_name)
            self.response.out.write(json.dumps({'player_id': pid}))
        except GameFull:
            self.response.out.write(json_error('Game already full'))

class StatusReport(webapp.RequestHandler):
    def get(self):
        """
        Returns the status of the game as a string
        <started>|<player_ids>|<player_penalties>|<game_size>
        """
        self.response.headers['Content-Type'] = 'application/json'
        game_id = self.request.get('game_id')

        game = games.get(game_id)
        
        if game is None:
            error_msg = json_error('No game with ID %s' % game_id)
            self.response.out.write(error_msg)
        else:    
            game_json = json_dumps(game.as_long_dict())
            self.response.out.write(game_json)
    
class UpdateRequest(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'
        game_id = self.request.get('game_id')
        game = games[game_id]
        player_id = self.request.get('player_id')
        penalties = game.get_penalties(player_id)
        
        if penalties:
            pen = penalties.popleft()
        else:
            pen = 0
            
        # Store the snapshot of the player's game
        snapshot = self.request.get('game_snapshot', '')
        game.store_snapshot(player_id, snapshot)
            
        self.response.out.write(json_dumps({'penalty': pen}))

class PartRequest(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'
        game_id = self.request.get('game_id')
        game = games[game_id]
        player_id = self.request.get('player_id')
        parts = game.get_parts(player_id)
        self.response.out.write(json_dumps(parts))
        
class UnregistrationRequest(webapp.RequestHandler):
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'
        game_id = self.request.get('game_id')
        game = games[game_id]
        player_id = self.request.get('player_id')
        
        if player_id in game.player_penalties:
            game.delete_player(player_id)
            self.response.out.write(json_info("Player %s deleted" % player_id))
        else:
            self.response.out.write(json_info("Player %s not found" % player_id))

class SendRequest(webapp.RequestHandler):
    def post(self):
        game_id = self.request.get('game_id')
        game = games[game_id]
        player_id = self.request.get('player_id')
        num_lines = self.request.get('num_lines')

        for player_key in game.player_penalties:
            if player_key != player_id:
                game.player_penalties[player_key].append(int(num_lines))

        info = json_info("Added a penalty of %s to all but %s" 
                         % (num_lines, player_id))
        self.response.out.write(info)

class MainPage(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('Welcome to the Entris server - hosted by Google App Engine')

URLS = [('/', MainPage),
        ('/new', NewGameRequest),
        ('/register', RegistrationRequest),
        ('/receive', UpdateRequest),
        ('/getparts', PartRequest),
        ('/sendlines', SendRequest),
        ('/unregister', UnregistrationRequest),
        ('/status', StatusReport),
        ('/list', ListGamesRequest)]

def main():
    application = webapp.WSGIApplication(URLS)
    run_wsgi_app(application)
            
if __name__ == '__main__':
    main()
    

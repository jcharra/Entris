
import web
import sys 
import time
from collections import deque
import threading
import random
import logging

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

   
class Game():
    def __init__(self, game_id, size):
        self.game_id = game_id
        
        self.player_penalties = {}
        self.screen_names = {}
        self.size = max(min(size, 10), 2)
        
        self.seconds_timeout_to_unregister = 5
        self.last_get_timestamp = {}
        
        # Game starts when all players have logged on
        self.started = False
        
        self.creation_timestamp = time.time()
    
    def add_player(self, screen_name):
        if self.started or len(self.player_penalties) >= self.size:
            raise GameFull("Joining no longer possible (Game started: %s)" % self.started)
            
        player_id = next_id(self.player_penalties)
        self.player_penalties[player_id] = deque()
        
        # Use default if screen name is missing
        self.screen_names[player_id] = (self.adjust_name(screen_name) 
                                        if screen_name else "player%s" % player_id)
        
        if self.is_full():
            for pid in self.player_penalties:
                self.last_get_timestamp[pid] = time.time()
            self.started = True
            
        #print "Added player %s to game %s" % (player_id, self.game_id)
        return player_id

    def delete_player(self, player_id):
        try:
            del self.player_penalties[player_id]
            del self.screen_names[player_id]
        except KeyError, err:
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
                    

GAME_TIMEOUT_IN_SECONDS = 600
def delete_finished_games():
    removable = []
    now = time.time()
    
    for game_id, game in games.items():
        if game.started:
            if not game.is_alive():
                # Started but no more players in it => remove it
                removable.append(game_id)
        else:
            # Not started but too old => remove it
            if now - game.creation_timestamp > GAME_TIMEOUT_IN_SECONDS:
                removable.append(game_id)
            
    for game_id in removable:
        del games[game_id]

MAX_GAME_NUMBER = 100
class NewGameRequest(webapp.RequestHandler):
    def get(self):
        
        # To avoid a separate job periodically deleting old (i.e. finished)
        # games, do the cleaning up here.
        delete_finished_games()
        
        self.response.headers['Content-Type'] = 'text/plain'
        
        if len(games) >= MAX_GAME_NUMBER:
            self.response.out.write('Server full!')
            return
            
        size = int(self.request.get('size', default_value="2"))
        game_id = next_id(games)
        game = Game(game_id, size)
        games[game_id] = game
        
        self.response.out.write(game_id)

class ListGamesRequest(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        game_repr = ["%s,%s,%s" % (game_id, game.size, game.player_penalties.keys())
                     for (game_id, game) in games.items()]
        self.response.out.write("|".join(game_repr))

class RegistrationRequest(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        game_id = self.request.get('game_id')
        
        # screen name may not be given
        screen_name = self.request.get('screen_name', None)
        
        game = games[game_id]
        try:
            # fetch a player id for the newbie
            pid = game.add_player(screen_name)
            self.response.out.write(pid)
        except GameFull, msg:
            self.response.out.write(msg)

class StatusReport(webapp.RequestHandler):
    def get(self):
        """
        Returns the status of the game as a string
        <started>|<player_ids>|<player_penalties>|<game_size>
        """
        self.response.headers['Content-Type'] = 'text/plain'
        game_id = self.request.get('game_id')

        game = games.get(game_id)
        
        if game is None:
            self.response.out.write('No game with ID %s' % game_id)
        else:    
            messages = []
            messages.append("Started: %s" % game.started)
            messages.append(",".join(game.screen_names.values()))
#            messages.append(",".join(game.player_penalties.keys()))
            messages.append(str(game.size))
            self.response.out.write("|".join(messages))
    
class UpdateRequest(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        game_id = self.request.get('game_id')
        game = games[game_id]
        player_id = self.request.get('player_id')
        penalties = game.get_penalties(player_id)
        if penalties:
            pen = penalties.popleft()
        else:
            pen = 0
            
        self.response.out.write("#%s#" % pen)
        
class UnregistrationRequest(webapp.RequestHandler):
    def post(self):
        self.response.headers['Content-Type'] = 'text/plain'
        game_id = self.request.get('game_id')
        game = games[game_id]
        player_id = self.request.get('player_id')
        
        if player_id in game.player_penalties:
            game.delete_player(player_id)
            self.response.out.write("Player %s deleted" % player_id)
        else:
            self.response.out.write("Player %s not found" % player_id)

class SendRequest(webapp.RequestHandler):
    def post(self):
        game_id = self.request.get('game_id')
        game = games[game_id]
        player_id = self.request.get('player_id')
        num_lines = self.request.get('num_lines')

        for player_key in game.player_penalties:
            if player_key != player_id:
                game.player_penalties[player_key].append(int(num_lines))

        self.response.out.write("Added a penalty of %s to all but %s" % 
                                (num_lines, player_id))

class MainPage(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('Welcome to the Entris server - hosted by Google Web Engine')

URLS = [('/', MainPage),
        ('/new', NewGameRequest),
        ('/register', RegistrationRequest),
        ('/receive', UpdateRequest),
        ('/sendlines', SendRequest),
        ('/unregister', UnregistrationRequest),
        ('/status', StatusReport),
        ('/list', ListGamesRequest)]

def main():
    application = webapp.WSGIApplication(URLS)
    run_wsgi_app(application)
            
if __name__ == '__main__':
    main()
    

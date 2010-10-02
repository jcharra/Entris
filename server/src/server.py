
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
        self.size = max(min(size, 10), 2)
        
        self.seconds_timeout_to_unregister = 5
        self.last_get_timestamp = {}
        
        # Game starts when all players have logged on
        self.active = False
        
    
    def add_player(self):
        if not self.active and len(self.player_penalties) < self.size:
            player_id = next_id(self.player_penalties)
            self.player_penalties[player_id] = deque()
        else:
            raise GameFull("Joining no longer possible (Game active: %s)" % self.active)
        
        if self.is_full():
            for pid in self.player_penalties:
                self.last_get_timestamp[pid] = time.time()
            self.active = True
            
        #print "Added player %s to game %s" % (player_id, self.game_id)
        return player_id

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
        for player, last_stamp in self.last_get_timestamp.items():
            if stamp - last_stamp > self.seconds_timeout_to_unregister:
                print "Kicking player %s due to timeout" % player
                del self.player_penalties[player]


class NewGameRequest(webapp.RequestHandler):
    def get(self):
        # a good time to remove all finished games.
        # implement later ...
        
        global games
        size = int(self.request.get('size', default_value="2"))
        game_id = next_id(games)
        game = Game(game_id, size)
        games[game_id] = game
        
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(game_id)

class RegistrationRequest(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        game_id = self.request.get('game_id')
        
        game = games[game_id]
        try:
            pid = game.add_player()
            self.response.out.write(pid)
        except GameFull, msg:
            self.response.out.write(msg)

class StatusReport(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        game_id = self.request.get('game_id')

        game = games.get(game_id)
        
        if game is None:
            self.response.out.write('No game with ID %s' % game_id)
        else:    
            messages = []
            messages.append("Started: %s" % game.active)
            messages.append(",".join(game.player_penalties.keys()))
            messages.append("Pending penalties: %s" % game.player_penalties)
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
            del game.player_penalties[player_id]
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
        ('/status', StatusReport)]

def main():
    application = webapp.WSGIApplication(URLS)
    run_wsgi_app(application)
            
if __name__ == '__main__':
    main()
    
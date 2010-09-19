
# OBSOLETE SERVER CODE
# Originally used for a web.py server to play Entris on.
# Won't work anymore, I'm afraid. The new server code 
# has been developed to run on Google App Engine.

import web
import sys 
import time
from collections import deque
import threading
import random

URLS = ('/new', 'NewGameRequest',
        '/register', 'RegistrationRequest',
        '/receive', 'UpdateRequest',
        '/sendlines', 'SendRequest',
        '/unregister', 'UnregistrationRequest',
        '/status', 'StatusReport',)

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

    
class Game(object):
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
            raise GameFull("Joining no longer possible")
        
        if self.is_full():
            for pid in self.player_penalties:
                self.last_get_timestamp[pid] = time.time()
            self.active = True
            
        print "Added player %s to game %s" % (player_id, self.game_id)
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


class NewGameRequest(object):
    def GET(self):
        # a good time to remove all finished games.
        # implement later ...
        
        try:
            
            size = int(web.input().size)
            game_id = next_id(games)
            game = Game(game_id, size)
            games[game_id] = game
            
            return game_id
    
        except AttributeError, att:
            return "Missing parameter: %s" % att
        except Exception, exc:
            return "Could not create game: %s" % exc
            
class RegistrationRequest(object):
    def GET(self):
        game_id = web.input().game_id
        
        try:
            game = games[game_id]
            pid = game.add_player()
            return pid
        except (GameFull, KeyError), exc:
            return str(exc)

class StatusReport(object):
    def GET(self):
        try:
            game_id = web.input().game_id
            game = games[game_id]
            
            messages = []
            messages.append("Started: %s" % game.active)
            messages.append(",".join(game.player_penalties.keys()))
            messages.append("Pending penalties: %s" % game.player_penalties)
            return "|".join(messages)
        except KeyError, err:
            return "Could not get status (Error: %s)" % err
    
class UpdateRequest(object):
    def GET(self):
        try:
            game_id = web.input().game_id
            game = games[game_id]
            player_id = web.input().player_id
            penalties = game.get_penalties(player_id)
            if penalties:
                return penalties.popleft()
            else:
                return "0"
        except KeyError, err:
            return "Receiving lines failed"
        
class UnregistrationRequest(object):
    def POST(self):
        try:
            input = web.input()
            game_id = input.game_id
            game = games[game_id]
            player_id = web.input().player_id
            
            if player_id in game.player_penalties:
                del game.player_penalties[player_id]
                return "Player %s deleted" % player_id
            else:
                return "Player %s not found" % player_id
        except Exception, exc:
            "Unregistering failed: %s" % exc

class SendRequest(object):
    def POST(self):
        try:
            input = web.input()
            game_id = input.game_id
            game = games[game_id]
            player_id, num_lines = input.player_id, input.num_lines

            for player_key in game.player_penalties:
                if player_key != player_id:
                    game.player_penalties[player_key].append(int(num_lines))
            return "Added a penalty of %s to all but %s" % (num_lines, player_id)
        except KeyError, err:
            return "Sending failed: %s" % err


class EntrisServer(threading.Thread):
    def run(self):
        app = web.application(URLS, globals())
        app.run()

def start_server():      
    app = web.application(URLS, globals()).run()
            
if __name__ == '__main__':
    start_server()
    
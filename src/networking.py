
import httplib
import urllib
import sys
import time
import threading
from collections import deque 

# TODO: Put this into a config file
GAME_SERVER = 'localhost:8090'
#GAME_SERVER = 'entrisserver.appspot.com'

class ServerNotAvailable(Exception):
    pass

def create_new_game(size, connection_str=GAME_SERVER):
    conn = httplib.HTTPConnection(connection_str)
    conn.request("GET", "/new?size=%s" % size)
    game_id = int(conn.getresponse().read())
    return game_id

POST_HEADERS = {"Content-type": "application/x-www-form-urlencoded",
                "Accept": "text/plain"}
    
class ServerEventListener(object):
    """
    Class responsible for all interaction with the game server,
    apart from game creation.
    
    Propagates info about lines received from other players to
    the game object, and has itself registered as an observer
    of the game, to get notified about lines to send.
    
    As long as its game is 'alive', the synchronisation thread
    of the ServerEventListener keeps asking the server for info
    and sending info in regular intervals of 1 second.
    """

    def __init__(self, game, online_game_id, host=GAME_SERVER, port=None):
        self.game = game
        self.game.add_line_observer(self)
        
        self.host, self.port = host, port
        self.game_id = online_game_id
        
        self.lines_to_send = deque()
        self.players = []
        
        # default, will be reset after first status update
        self.game_size = 2
        
        self.connection = None
        self.connect_to_game()
        self.abort = False
        
        assert self.game_id, 'No game id provided'

    def listen(self):
        self.updateThread = threading.Thread(target=self.synchronize)
        self.updateThread.start()

    def synchronize(self):
        while not self.abort:
            self.update_players_list()
            time.sleep(1)
            if self.ask_for_start_permission():
                break

        # We have to update the player list once more, otherwise
        # the game might be "started", and we see a winning screen
        # because we falsely realize there are no players but us.
        self.update_players_list()
        self.game.started = True
        
        while not self.abort and not self.game.gameover:
            time.sleep(1)

            self.get_lines()
            self.send_lines()
            self.update_players_list()
         
        self.unregister_from_server()
        
    def unregister_from_server(self):
        params = urllib.urlencode({'game_id': self.game_id,
                                   'player_id': self.player_id})
        self.connection.request("POST", "/unregister", params, POST_HEADERS)
        
        print self.connection.getresponse().read()

    def ask_for_start_permission(self):    
        self.connection.request("GET", "/status?game_id=%s" % self.game_id)
        status = self.connection.getresponse().read()
        # TODO: Parse status report and put it into a GameStatus object
        return status.startswith("Started: True")
    
    def update_players_list(self):
        try:
            self.connection.request("GET", "/status?game_id=%s" % self.game_id)
            status_string = self.connection.getresponse().read()
            # TODO: Parse status report and put it into a GameStatus object
            status, players, size = status_string.split('|')[:3]        
            self.players = players.split(",")
            self.game_size = int(size)
        except (httplib.CannotSendRequest, ValueError), err:
            print ("Status fetching for game %s failed. (%s)" 
                   % (self.game_id, err))
    
    def get_lines(self):
        params = urllib.urlencode({'game_id': self.game_id,
                                   'player_id': self.player_id})
        
        try:
            self.connection.request("GET", "/receive?%s" % params)
            lines_received = int(self.connection.getresponse().read().strip('#'))
            
            if lines_received:
                print "Ouch! Received %s lines" % lines_received
                self.game.regurgitate(lines_received)
        except (httplib.CannotSendRequest, ValueError), err:
            print "Getting lines failed: %s" % err
                
    def send_lines(self):
        if not self.lines_to_send:
            return
    
        try:
            lines = self.lines_to_send[0]
            params = urllib.urlencode({'game_id': self.game_id,
                                       'player_id': self.player_id,
                                       'num_lines': lines})
            self.connection.request("POST", "/sendlines", params, POST_HEADERS)
            response = self.connection.getresponse().read()
            
            if response.startswith('Added a penalty'):
                # If it worked, remove the element from the deque
                self.lines_to_send.popleft()
            else:
               raise httplib.CannotSendRequest('Sending failed with response %s' % response)
                
        except (httplib.CannotSendRequest, Exception), exc:
            print "Errors while sendling lines to the server (%s)" % exc

    def notify(self, number_of_lines):
        print "Been notified of %s lines" % number_of_lines
        self.lines_to_send.append(number_of_lines)
    
    def get_number_of_players_missing(self):
        return self.game_size - len(self.players)
        
    def connect_to_game(self):
        connection_str = self.host
        if self.port:
            connection_str += ":%s" % self.port

        attempts = 0
        while attempts < 10:
            try:
                self.connection = httplib.HTTPConnection(connection_str)
                self.connection.request("GET", "/register?game_id=%s" % self.game_id)
                self.player_id = self.connection.getresponse().read()

                return
            except Exception, exc:
                print "Connection/registration failed: %s" % exc
                time.sleep(1)
                attempts += 1
                
        raise ServerNotAvailable("Could not register at %s" % connection_str)
        
if __name__ == '__main__':
    import server

    server_thread = threading.Thread(target=server.start_server)
    server_thread.start()
    time.sleep(1)
    
    from gamemodel import Game
    game1 = Game((10, 10), 0.1)
    game2 = Game((10, 10), 0.1)
    
    sel1 = ServerEventListener(game1, "0.0.0.0", 8080)
    sel1.listen()
    
    sel2 = ServerEventListener(game2, "0.0.0.0", 8080)
    sel2.listen()
    
    game1.delete_rows([0])
    
    time.sleep(4)
    game2.proceed()
    game2.proceed()
    assert any(game2.cells[-10:]), "Nothing showed up in other game: \n%s" % game2
    
    
    
    
    
    

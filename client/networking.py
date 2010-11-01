
import httplib
import urllib
import time
import threading
from collections import deque 
from events import LinesDeletedEvent

# TODO: Put this into a config file
GAME_SERVER = 'localhost:8090'
#GAME_SERVER = 'entrisserver.appspot.com'

class ConnectionFailed(Exception):
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
    
    Constructor expects a 'screen name' for the player to send
    to the server.
    """

    def __init__(self, game, online_game_id, screen_name, host=GAME_SERVER):
        self.game = game
        self.game.add_observer(self)
        
        self.host = host
        self.game_id = online_game_id
        self.screen_name = screen_name
        
        self.lines_to_send = deque()
        self.players = []
        self.player_game_snapshots = {}
        
        # default, will be reset after first status update
        self.game_size = 2
        
        self.connection = None
        self.connect_to_game()
        
        assert self.game_id, 'No game id provided'

    def listen(self):
        self.updateThread = threading.Thread(target=self.synchronize)
        self.updateThread.start()

    def synchronize(self):
        while not self.game.aborted:
            self.update_players_list()
            time.sleep(1)
            if self.ask_for_start_permission():
                break

        # We have to update the player list once more, otherwise
        # the game might be "started", and we see a winning screen
        # because we falsely realize there are no players but us.
        self.update_players_list()
        self.game.started = True
        
        while (not self.game.aborted 
               and not self.game.gameover
               and not self.game.victorious):
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
            started, players, size, snapshots = status_string.split('|')[:4]        
            self.players = players.split(",")
            self.game_size = int(size)
        except (httplib.CannotSendRequest, ValueError), err:
            print ("Status fetching for game %s failed."
                   " Status string was %s"
                   " Error msg: %s" 
                   % (self.game_id, status_string, err))

        snapshot_list = snapshots.split(';')
        try:
            self.player_game_snapshots = dict(elem.split(':') 
                                              for elem in snapshot_list)
        except ValueError:
            self.player_game_snapshots = {}
        
    
    def get_lines(self):
        """
        This request is sent periodically to the server, in
        order to receive penalties from other players.
        
        To 'authorize' the request, the client sends a snapshot
        of his game in a compressed format.
        """
        
        params = urllib.urlencode({'game_id': self.game_id,
                                   'player_id': self.player_id,
                                   'game_snapshot': self.game.compressed_repr()})
        
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
            print "Errors while sending lines to the server (%s)" % exc

    def notify(self, event):
        if isinstance(event, LinesDeletedEvent):
            print "Been notified of %s lines" % event.number_of_lines
            self.lines_to_send.append(event.number_of_lines)
        else:
            # We don't care for other events
            pass
    
    def get_number_of_players_missing(self):
        return self.game_size - len(self.players)
        
    def connect_to_game(self):
        connection_str = self.host

        attempts = 0
        while attempts < 3:
            try:
                self.connection = httplib.HTTPConnection(connection_str)
                self.connection.request("GET", "/register?game_id=%s&screen_name=%s" 
                                        % (self.game_id, self.screen_name))
                self.player_id = int(self.connection.getresponse().read())

                return
            except Exception, exc:
                print "Connection/registration failed: %s" % exc
                time.sleep(1)
                attempts += 1
                
        raise ConnectionFailed("Could not register at %s" % connection_str)
    
    
    
    
    
    

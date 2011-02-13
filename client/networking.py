
import httplib
import urllib
import time
import threading
import logging
import socket

try:
    import json
except ImportError:
    import simplejson as json 

from collections import deque 
from events import LinesDeletedEvent
from monitoring import compress
from config import GAME_SERVER

class ConnectionFailed(Exception):
    pass

POST_HEADERS = {"Content-type": "application/x-www-form-urlencoded",
                "Accept": "text/plain"}

def initialize_network_game(config):
    conn = httplib.HTTPConnection(GAME_SERVER)
    params = urllib.urlencode(config)
    conn.request("POST", "/new" , params, POST_HEADERS)
    response = conn.getresponse().read()
    return json.loads(response)
       
   
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

    CANNOT_CONNECT_MSG = "Cannot connect to server"

    def __init__(self, game, online_game_id, screen_name, host=GAME_SERVER):
        self.game = game
        self.game.add_observer(self)
        
        self.host = host
        self.game_id = online_game_id
        self.screen_name = screen_name
        self.player_id = None
        
        self.lines_to_send = deque()
        self.players = {}
        self.player_game_snapshots = {}
        
        self.game_size = None
        
        # Any error messages that are returned by our server
        # will be stored here. Someone else must take care of
        # displaying them somewhere.
        self.error_msg = ""  
        
        self.connection = None
        self.connect_to_game()
        
    def listen(self):
        if not self.connection:
            self.error_msg = self.CANNOT_CONNECT_MSG
        else:
            self.updateThread = threading.Thread(target=self._synchronize)
            self.updateThread.start()

    def _synchronize(self):
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
        
        try:
            self.connection.request("POST", 
                                    "/unregister", 
                                    params, 
                                    POST_HEADERS)
            logging.info(self.connection.getresponse().read()) 
        except Exception:
            # That's not too bad ...
            logging.info("Unregistration failed")
            pass            

    def ask_for_start_permission(self):
        try:    
            self.connection.request("GET", "/status?game_id=%s" % self.game_id)
            game_info = json.loads(self.connection.getresponse().read())
            return game_info['started']
        except:
            self.error_msg = self.CANNOT_CONNECT_MSG
        
    def update_players_list(self):
        try:
            self.connection.request("GET", "/status?game_id=%s" % self.game_id)
            game_info = json.loads(self.connection.getresponse().read())
            self.game_size = game_info['size']
        except Exception:
            self.error_msg = "Cannot fetch game data from server"
            return

        try:
            self.players = game_info['screen_names']
            self.player_game_snapshots = game_info['snapshots']
        except KeyError:
            self.players = {}
            self.player_game_snapshots = {}          
        
        # If we get here, everything should be okay,
        # so clear the error message
        self.error_msg = ""
    
    def get_lines(self):
        """
        This request is sent periodically to the server, in
        order to receive penalties from other players.
        
        To 'authorize' the request, the client sends a snapshot
        of his game in a compressed format.
        """
        
        params = urllib.urlencode({'game_id': self.game_id,
                                   'player_id': self.player_id,
                                   'game_snapshot': compress(self.game)})
        
        try:
            self.connection.request("GET", "/receive?%s" % params)
            penalty_info = json.loads(self.connection.getresponse().read())
            lines_received = penalty_info['penalty']
            
            if lines_received:
                print "Ouch! Received %s lines" % lines_received
                self.game.regurgitate(lines_received)
        except (httplib.CannotSendRequest, ValueError), err:
            # Not too bad ... but we must take care that we
            # don't miss fetching our penalties for too long,
            # otherwise we might get dismissed from the game.
            logging.info("Getting lines failed: %s" % err)
                            
    def send_lines(self):
        if not self.lines_to_send:
            return
    
        try:
            lines = self.lines_to_send[0]
            params = urllib.urlencode({'game_id': self.game_id,
                                       'player_id': self.player_id,
                                       'num_lines': lines})
            self.connection.request("POST", "/sendlines", params, POST_HEADERS)
            response = json.loads(self.connection.getresponse().read())
            
            if response["info"].startswith("Added"):
                # If it worked, remove the element from the deque
                self.lines_to_send.popleft()
            else:
                raise httplib.CannotSendRequest('Sending failed with response %s' % response)
                
        except (httplib.CannotSendRequest, Exception), exc:
            logging.info("Errors while sending data to server (%s)" % exc)

    def get_next_parts(self):
        params = urllib.urlencode({'game_id': self.game_id,
                                   'player_id': self.player_id})
        try:
            self.connection.request("GET", "/getparts?%s" % params)
            return json.loads(self.connection.getresponse().read())
        except:
            # This may fail from time to time ...
            return []

    def notify(self, event):
        if isinstance(event, LinesDeletedEvent):
            print "Been notified of %s lines" % event.number_of_lines
            self.lines_to_send.append(event.number_of_lines)
        else:
            # We don't care for other events
            pass
    
    def get_number_of_players_missing(self):
        return (self.game_size - len(self.players)
                if self.game_size is not None
                else 0)
    
    def connect_to_game(self):
        connection_str = self.host

        attempts = 0
        while attempts < 3:
            try:
                self.connection = httplib.HTTPConnection(connection_str)
                self.connection.request("GET", "/register?game_id=%s&screen_name=%s" 
                                        % (self.game_id, self.screen_name))
                response = json.loads(self.connection.getresponse().read())
                self.player_id = response['player_id']

                return
            except (socket.error, Exception), exc:
                logging.warn("Connection failed: %s" % exc)
                self.connection = None
                time.sleep(1)
                attempts += 1
                
        self.error_msg = "Could not connect to server"
    
    
    
    
    
    

import urllib
import time
import threading
import logging
import json
import http.client
import codecs
from collections import deque

from events import LinesDeletedEvent
from monitoring import compress

logger = logging.getLogger("networking")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


class ConnectionFailed(Exception):
    pass


POST_HEADERS = {"Content-type": "application/x-www-form-urlencoded",
                "Accept": "text/plain"}

DEFAULT_SERVER = "entris.charra.de"


# DEFAULT_SERVER = "localhost:8888"


def initialize_network_game(config):
    server_address = config['server_name']
    if ":" in server_address:
        host, port = server_address.split(":")
        conn = http.client.HTTPConnection(host, int(port))
    else:
        conn = http.client.HTTPConnection(server_address)

    params = urllib.parse.urlencode(config)
    conn.request("POST", "/new", params, POST_HEADERS)
    rawresponse = conn.getresponse().read()
    return json.loads(rawresponse.decode())


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

    def __init__(self, game, online_game_id, screen_name, host):
        self.game = game
        self.game.add_observer(self)

        self.host = host
        self.game_id = online_game_id
        self.screen_name = screen_name
        self.player_id = None

        self.lines_to_send = deque()
        self.players = {}
        self.player_game_snapshots = {}
        self.players_alive = 0

        self.game_size = None

        # Any error messages that are returned by our server
        # will be stored here. Someone else must take care of
        # displaying them somewhere.
        self.error_msg = ""

        self.response_reader = codecs.getreader("utf-8")
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
        params = urllib.parse.urlencode({'game_id': self.game_id,
                                         'player_id': self.player_id})

        try:
            self.connection.request("POST",
                                    "/unregister",
                                    params,
                                    POST_HEADERS)
            resp_json = json.load(self.response_reader(self.connection.getresponse()))
            logging.info(resp_json)
        except Exception:
            # That's not too bad ...
            logging.info("Unregistration failed")
            pass

    def ask_for_start_permission(self):
        try:
            self.connection.request("GET", "/status?game_id=%s" % self.game_id)
            game_info = json.load(self.response_reader(self.connection.getresponse()))
            return game_info['started']
        except:
            self.error_msg = self.CANNOT_CONNECT_MSG

    def update_players_list(self):
        try:
            self.connection.request("GET", "/status?game_id=%s" % self.game_id)
            game_info = json.load(self.response_reader(self.connection.getresponse()))
            self.game_size = game_info['size']
        except Exception as ex:
            logger.error("Update failed %s", ex)
            self.error_msg = "Cannot fetch game data from server"
            return

        try:
            player_infos = game_info['screen_names']

            count_alive = 0
            for info in player_infos:
                self.players[info['player_id']] = info['player_id']
                self.player_game_snapshots[info['player_id']] = info['snapshot']
                if info["alive"]:
                    count_alive += 1
            self.players_alive = count_alive

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

        params = urllib.parse.urlencode({'game_id': self.game_id,
                                         'player_id': self.player_id,
                                         'game_snapshot': compress(self.game)})

        try:
            self.connection.request("GET", "/receive?%s" % params)
            response = self.connection.getresponse()
            penalty_info = json.load(self.response_reader(response))
            lines_received = penalty_info['penalty']

            if lines_received:
                logging.info("Ouch! Received %s lines" % lines_received)
                self.game.regurgitate(lines_received)
        except (http.client.CannotSendRequest, ValueError) as ex:
            # Not too bad ... but we must take care that we
            # don't miss fetching our penalties for too long,
            # otherwise we might get dismissed from the game.
            logger.info("Getting lines failed: %s", ex)

    def send_lines(self):
        if not self.lines_to_send:
            return

        try:
            lines = self.lines_to_send[0]
            params = urllib.parse.urlencode({'game_id': self.game_id,
                                             'player_id': self.player_id,
                                             'num_lines': lines})
            self.connection.request("POST", "/sendlines", params, POST_HEADERS)
            response = json.load(self.response_reader(self.connection.getresponse()))

            if response["info"].startswith("Added"):
                # If it worked, remove the element from the deque
                self.lines_to_send.popleft()
            else:
                raise http.client.CannotSendRequest('Sending failed with response %s' % response)

        except (http.client.CannotSendRequest, Exception):
            logging.info("Errors while sending data to server")

    def get_next_parts(self):
        params = urllib.parse.urlencode({'game_id': self.game_id,
                                         'player_id': self.player_id})
        try:
            self.connection.request("GET", "/getparts?%s" % params)
            return json.load(self.response_reader(self.connection.getresponse()))
        except:
            # This may fail from time to time ...
            return []

    def notify(self, event):
        if isinstance(event, LinesDeletedEvent):
            logging.info("Been notified of %s lines" % event.number_of_lines)
            self.lines_to_send.append(event.number_of_lines)
        else:
            # We don't care for other events
            pass

    def get_number_of_players_missing(self):
        return (self.game_size - len(self.players)
                if self.game_size is not None
                else 0)

    def connect_to_game(self):
        attempts = 0
        while attempts < 3:
            try:
                server_address = self.host
                if ":" in server_address:
                    host, port = server_address.split(":")
                    self.connection = http.client.HTTPConnection(host, int(port))
                else:
                    self.connection = http.client.HTTPConnection(server_address)

                self.connection.request("GET", "/register?game_id=%s&screen_name=%s"
                                        % (self.game_id, self.screen_name))

                response = self.connection.getresponse()
                json_response = json.load(self.response_reader(response))
                self.player_id = json_response['player_id']

                return
            except Exception as ex:
                logging.warning("Connection failed: {}".format(ex))
                self.connection = None
                time.sleep(1)
                attempts += 1

        self.error_msg = "Could not connect to server"

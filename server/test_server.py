import httplib
import urllib
import unittest
#import server
import time

class ServerTest(unittest.TestCase):
    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Accept": "text/plain"}

    def setUp(self):
        self.conn = httplib.HTTPConnection('localhost:8090')

        # create a new game
        self.conn.request("GET", "/new?size=5")
        self.game_id = int(self.conn.getresponse().read())

        self.player_ids = []

        # add five players
        for _ in range(5):
            self.conn.request("GET", "/register?game_id=%s" % self.game_id)
            player_id = int(self.conn.getresponse().read())
            self.player_ids.append(player_id)

    def tearDown(self):
        self.conn.close()

    def test_too_many_players(self):
        self.conn.request("GET", "/register?game_id=%s" % self.game_id)
        resp = self.conn.getresponse().read()
        assert resp.startswith("Joining no longer possible"), "Joining unexpectedly succeeded: '%s'" % resp

    def test_get_status(self):
        self.conn.request("GET", "/status?game_id=%s" % self.game_id)
        resp = self.conn.getresponse().read()
        assert resp.startswith("Started: True"), "Status fetching fails"

    def test_send_and_get_lines(self):
        for pid in self.player_ids:
            self.conn.request("GET", "/receive?game_id=%s&player_id=%s" % (self.game_id, pid))
            resp = int(self.conn.getresponse().read().strip('#'))
            assert resp == 0, "Penalty found where not expected: %s" % resp

        for num_lines, pid in enumerate(self.player_ids):    
            params = urllib.urlencode({'game_id': self.game_id, 
                                       'player_id': pid, 
                                       'num_lines': num_lines})
            self.conn.request("POST", "/sendlines", params, self.headers)
            resp = self.conn.getresponse().read()
            assert resp == "Added a penalty of %s to all but %s" % (num_lines, pid), "Response was %s" % resp

        for pid in self.player_ids:
            self.conn.request("GET", "/receive?game_id=%s&player_id=%s" % (self.game_id, pid))
            resp = int(self.conn.getresponse().read().strip('#'))
            assert resp in range(4), "Invalid penalty found: %s" % resp

    def test_unregistration(self):
        params = urllib.urlencode({'game_id': self.game_id, 
                                   'player_id': self.player_ids[0]})
        self.conn.request("POST", "/unregister", params, self.headers)
        resp = self.conn.getresponse().read()
        
        assert resp == "Player %s deleted" % self.player_ids[0], "Unregistration said %s" % resp
    
    def test_part_generator(self):
        self.conn.request("GET", "/getparts?game_id=%s&player_id=%s" % (self.game_id, self.player_ids[0]))
        parts = [int(x) for x in self.conn.getresponse().read().split(",")]
        
        assert len(parts) == 10, "Not enough parts received"
        assert [p for p in parts if p in range(0, 8)] == parts, "Bad range %s" % parts
    
        # Get the other player's parts ... they must be identical!
        self.conn.request("GET", "/getparts?game_id=%s&player_id=%s" % (self.game_id, self.player_ids[1]))
        parts_two = [int(x) for x in self.conn.getresponse().read().split(",")]
        assert parts == parts_two, "Unfair game, received different parts: %s, %s" % (parts, parts_two)
    
    def test_timeout(self):
        # Provoke timeout
        time.sleep(6)

        # This request should now cause all players to be kicked ...
        self.conn.request("GET", "/receive?game_id=%s&player_id=%s" % (self.game_id, self.player_ids[0]))
        print self.conn.getresponse().read()
        
        self.conn.request("GET", "/status?game_id=%s" % self.game_id)
        resp = self.conn.getresponse().read()
        players = resp.split('|')[1]
        assert players == '', "Status fetching fails: %s" % resp


if __name__ == '__main__':
    # start server outside the test suite
    #server_thread = threading.Thread(target=server.main)
    #server_thread.start()

    # wait for the server to get up and running
    #time.sleep(1)
        
    unittest.main()

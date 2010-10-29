import httplib
import urllib
import threading
import unittest
import server
import time

class ServerTest(unittest.TestCase):
    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Accept": "text/plain"}

    def setUp(self):
        self.conn = httplib.HTTPConnection('0.0.0.0:8080')

        # create a new game
        self.conn.request("GET", "/new?size=5")
        self.game_id = int(self.conn.getresponse().read())

        self.player_ids = []

        # add five players
        for i in range(5):
            self.conn.request("GET", "/register?game_id=%s" % self.game_id)
            player_id = int(self.conn.getresponse().read())
            self.player_ids.append(player_id)

    def tearDown(self):
        self.conn.close()

    def test_too_many_players(self):
        self.conn.request("GET", "/register?game_id=%s" % self.game_id)
        resp = self.conn.getresponse().read()
        assert resp == "Joining no longer possible", "Joining unexpectedly succeeded: '%s'" % resp

    def test_get_status(self):
        self.conn.request("GET", "/status?game_id=%s" % self.game_id)
        resp = self.conn.getresponse().read()
        assert resp.startswith("Started: True"), "Status fetching fails"

    def test_send_and_get_lines(self):
        for pid in self.player_ids:
            self.conn.request("GET", "/receive?game_id=%s&player_id=%s" % (self.game_id, pid))
            resp = int(self.conn.getresponse().read())
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
            resp = int(self.conn.getresponse().read())
            assert resp in range(4), "Invalid penalty found: %s" % resp

    def test_unregistration(self):
        params = urllib.urlencode({'game_id': self.game_id, 
                                   'player_id': self.player_ids[0]})
        self.conn.request("POST", "/unregister", params, self.headers)
        resp = self.conn.getresponse().read()
        
        assert resp == "Player %s deleted" % self.player_ids[0], "Unregistration said %s" % resp
    
    def test_timeout(self):
        # Provoke timeout
        time.sleep(5)

        # This request should now cause all players to be kicked ...
        self.conn.request("GET", "/receive?game_id=%s&player_id=%s" % (self.game_id, self.player_ids[0]))
        print self.conn.getresponse().read()
        
        self.conn.request("GET", "/status?game_id=%s" % self.game_id)
        resp = self.conn.getresponse().read()
        status, players, penalties = resp.split('|')[:3]
        assert players == '', "Status fetching fails: %s" % resp


if __name__ == '__main__':
    # start server outside the test suite
    server_thread = threading.Thread(target=server.start_server)
    server_thread.start()

    # wait for the server to get up and running
    time.sleep(1)
        
    unittest.main()
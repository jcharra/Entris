---------------------------------
ENTRIS - an enhanced Tetris clone 
---------------------------------

Written in August/September 2010 by Johannes Charra using 
Python2.6 and consequently excessive duck typing (pun intended).


Controls
--------

Arrow keys move and accelerate the current piece.
A/S rotates the piece clockwise/counterclockwise.
ESC aborts the game and gets you back to the config screen.


Config screen
-------------

Here you may choose

 - the size of the game window
 - the size of the game grid.
 - the probability of the evil duck appearing (0% will make it
   an enjoyable traditional Tetris, whereas the maximum value of 
   10% will have you quacked to death within minutes)
 - to play single player
 - to create or join an online multiplayer game

Use the left/right arrow keys to modify the respective selection.
Selecting START and press ENTER to play.


Playing online
--------------

To create an online game, you have to provide the number of players
it's supposed to wait for (including yourself). After that, Entris
tries to establish a connection to the game server, which is currently
hosted by Google App Engine (entrisserver.appspot.com).

If the connection has been established correctly, you see the empty 
game screen waiting for the game to start (i.e. you wait for the empty
player slots to fill up). As soon as everybody has joined, the game starts.

To join an online game, you need to be told the game ID by the one who 
started the game. It is shown on the bottom right of the game window.


Open bugs
---------

 - Music cutoff one note too early
 - Segmentation fault when playing two subsequent games
   with different screen resolutions
 - Sporadic rotation errors (disallowed moves possible)


Planned improvements
--------------------

 - Change music with each level
 - Improve tests in each modules (esp. the server stuff should
   tell us when it failed)
 - Implement sound effect for rotating the piece/moving down
 
 
Etymology
---------

"Entris" stems from the German word for duck - "Ente".

Enjoy playing!



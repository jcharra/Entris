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

Press ENTE-R to modify the respective selection.


Open bugs
---------

 - Music cutoff one note too early
 - Segmentation fault when playing two subsequent games
   with different screen resolutions
 - Sporadic rotation errors (disallowed moves possible)
 - Server connection appears unstable


Planned improvements
--------------------

 - Make penalty rows easier to fill up (e.g. one or two free squares
   per line instead of the checkered pattern)
 - Change music with each level
 - Improve tests in each modules (esp. the server stuff should
   tell us when it failed)
 - Implement visual/sound effects for deletion of lines
 - Implement sound effect for rotating the piece/moving down
 
 
Etymology
---------

"Entris" stems from the German word for duck - "Ente".

Enjoy playing!



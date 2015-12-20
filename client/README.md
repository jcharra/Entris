ENTRIS - an enhanced Tetris clone 
=================================

Developed in 2010 and 2011 by Johannes Charra using 
Python and consequently excessive duck typing (pun intended).

License
=======

Entris is published under the GNU General Public License.

Requirements
============

You need to have Pygame installed (http://pygame.org) and a 32-bit Python. 


Controls
========

LEFT, RIGHT, DOWN keys move/accelerate the current piece.
UP rotates the piece counterclockwise (as an alternative to A/S).
A/S rotates the piece clockwise/counterclockwise.
ESC aborts the game and gets you back to the config screen.


Start Menu
==========

After typing your player name you may choose to

 - Start a single player game
 - Create a multiplayer game
 - Join a multiplayer game

Single player game
==================

To create a single player game you have to specify

 - the size of the game grid
 - the duck probability, ranging from 0% to 10%, i.e.
   the probability that a duck appears. 0% will result 
   in a boring standard Tetris game, so you may want to 
   choose a higher probability here. 

Creating an online game
=======================

When creating an online game you have to specify

 - the size of the game grid
 - the expected number of players involved
 - the duck probability, ranging from 0% to 10% (cf. single player
   game configuration)

Joining an online game
======================

If you choose to join an existing online game, you will 
be taken to the Entris lobby, where the existing games are
listed with their properties, i.e. the number of player involved,
the duck probability and the game size. The number of "open slots" 
is visible for each game, indicating the number of players missing
for the game to start. Choose a game here of return to the previous
menu by hitting ESC. Maybe you want to create your own game. 

 
Etymology
=========

"Entris" stems from the German word for duck - "Ente".

Enjoy playing!



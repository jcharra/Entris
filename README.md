Entris
======

Tetris clone featuring the evil duck

Components
==========

Entris has a server component that's prepared to run on a Google app engine server. There has been an instance 
running at http://entrisserver.appspot.com/ but that one has been down for a while. I'm planning a rewrite in Go.

The client component resides in the "client" subdirectory.

The server code can be found in the "server" subdirectory. It's extremely simple and has never been pushed to its limits, it probably doesn't scale too well.
UPDATE 02/2016: The Python version of the server has been deprecated and replaced with a reimplementation in Go, to be found at https://github.com/jcharra/go-entrisserver

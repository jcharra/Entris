Entris
======

Multiplayer Tetris clone featuring the evil duck. Challenge up to 4 friends to play online.

Installation
============

You need Python2 ad pygame to play. Install python, then type

```
pip install pygame
```

and you should be ready to go.

Client
======

The client component resides in the "client" subdirectory. It can be run with

```
python entris.py
```

Server
======

A game server you can connect to is running at entris.charra.de

As for the code: The server component used to run on a Google app engine server and was originally implemented in Python,
but as of 02/2016, the Python version has been deprecated and replaced with a reimplementation in Go,
which can be found at

https://github.com/jcharra/go-entrisserver

The deprecated Python server code remains in the "server" subdirectory.
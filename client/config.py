
"""
Module for Entris-specific config
"""

GAME_TYPE_OPTIONS = (('single', 'Single player'),
                     ('create', 'Create online game'),
                     ('join', 'Join online game'))
    
GAME_SIZE_OPTIONS = [((x, y), "Grid size: %s x %s" % (x, y))
                      for (x, y) in ((20, 25), (25, 32), (30, 40))]

DUCK_PROB_OPTIONS = [(i/100.0, "Duck probability: %i%%" % i) 
                     for i in range(11)]

PLAYER_NUMBER_OPTIONS = [(i, "%i players" % i) 
                         for i in range(2, 6)]

#GAME_SERVER = 'entrisserver.appspot.com'
GAME_SERVER = 'localhost:8090'

GAME_WINDOW_DIMENSIONS = (450, 600) 
SCREEN_DIMENSIONS = (800, 600)

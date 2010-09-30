
import pygame
pygame.mixer.init()

import os
import random
from events import QuackEvent, LinesDeletedEvent

SOUND_DIR = '../sound'

class SoundManager(object):
    def __init__(self):
        self.quack = pygame.mixer.Sound('%s/quack.ogg' % SOUND_DIR)
        # TODO: Create and use a DIFFERENT sound
        #self.delete_sound = pygame.mixer.Sound('%s/quack.ogg' % SOUND_DIR)
    
    def play_background_music(self):
        variations = ["%s/%s" % (SOUND_DIR, var) 
                      for var in os.listdir(SOUND_DIR) 
                      if var.startswith('var')]
        random.shuffle(variations)
        
        pygame.mixer.music.load(variations[0])
        pygame.mixer.music.play()

        # put the rest into the playlist ... that should suffice :)
        # FIXME: Doesn't work as expected. Just one piece played,
        # cut off right before the last note.
        for var in variations[1:]:
            pygame.mixer.music.queue(var)
        
    def stop_background_music(self):
        pygame.mixer.music.fadeout(100)
        
    def notify(self, event_type):
        if isinstance(event_type, QuackEvent):
            # A duck hath appeared ... so quack!
            self.quack.play()
        elif isinstance(event_type, LinesDeletedEvent):
            #self.delete_sound.play()
            pass
        else:
            raise KeyError('No behaviour defined for event type %s' % type(event))

import pygame
pygame.mixer.init()

import os
import random
from events import QuackEvent, LinesDeletedEvent

SOUND_DIR = 'sound'

class SoundManager(object):
    def __init__(self):
        self.quack = pygame.mixer.Sound('%s/quack.ogg' % SOUND_DIR)
        # TODO: Create and use a DIFFERENT sound
        #self.delete_sound = pygame.mixer.Sound('%s/quack.ogg' % SOUND_DIR)
    
    def play_background_music(self):
        music_file = os.path.join(SOUND_DIR, "kraut.mid")
        pygame.mixer.music.load(music_file)
        pygame.mixer.music.play()
        
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
            raise KeyError('No behaviour defined for event type %s' % event_type)
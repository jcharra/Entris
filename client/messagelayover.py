
import pygame

class TransparentLayover(pygame.Surface):
    '''
    Class representing a layover for another surface.
    '''

    def __init__(self, background_surface):
        self.dimensions = background_surface.dimensions
        pygame.Surface.__init__(self, self.dimensions)
        
        self.background_surface = background_surface
        
    def render_message(self, message, fontsize=14, fade=False):
        if fade:
            self.set_alpha(10)
            background_color = (50, 50, 50)   
        else:
            background_color = (0, 0, 0)
        
        self.fill(background_color)
        
        self.font = pygame.font.Font("jack_type.ttf", fontsize)
        
        # TODO: Implement handling of line breaks
        text = self.font.render(message, True, (255, 0, 0), background_color)
        coords = (self.dimensions[0]/2 - text.get_width()/2, 
                  self.dimensions[1]/2 - text.get_height()/2)
        
        self.blit(text, coords)
        self.background_surface.blit(self, (0, 0))

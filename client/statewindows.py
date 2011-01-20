
import pygame
pygame.init()
from pygame.locals import K_ESCAPE, K_RETURN, K_RIGHT, K_LEFT, K_BACKSPACE, K_DOWN, K_UP

DEFAULT_FONT = pygame.font.Font('jack_type.ttf', 18) 
DEFAULT_FONT_COLOR = (0, 255, 0) 

class StateWindow(pygame.Surface):
    def __init__(self, dimensions):
        pygame.Surface.__init__(self, dimensions)
        
        self.finished = False
        self.aborted = False
        self.successor = None
        self.predecessor = None

        self.font = DEFAULT_FONT
        self.font_color = DEFAULT_FONT_COLOR
                
    def render(self):
        raise NotImplementedError()
    
    def handle_keypress(self, key):
        if key == K_ESCAPE:
            self.aborted = True
            
    def handle_keyrelease(self, key):
        pass
            
    def proceed(self, milliseconds):
        pass

    def set_successor(self, succ):
        self.successor = succ
        succ.predecessor = self
        
    def get_successor(self):
        return self.successor
    
    def as_dict(self):
        return {}
    
    def collect_dicts(self):
        d = {}
        node = self
        while node:
            d.update(node.as_dict())
            node = node.get_successor()
        return d

class MenuItem(object):

    def __init__(self, key, value_items):
        self.key = key
        
        self.value_items = value_items
        self.selected_index = 0
        
    @property
    def text(self):
        return self.value_items[self.selected_index][1]
            
    def get_value(self):
        return self.value_items[self.selected_index][0]
    
    def rotate(self, diff):
        self.selected_index = (self.selected_index + diff) % len(self.value_items)
 
class MenuWindow(StateWindow):
    def __init__(self, dimensions):
        StateWindow.__init__(self, dimensions)
        self.items = []
        self.title = ''
        self.bottom_hint = ''
        self.selected_index = 0
        
    def add_items(self, *items):
        """
        Add a bunch of MenuItem instances
        """
        self.items.extend(items)
    
    def as_dict(self):
        return dict((item.key, item.get_value())
                    for item in self.items)
    
    def handle_keypress(self, key):
        if key == K_RETURN:
            self.finished = True
        elif key == K_LEFT:
            self.items[self.selected_index].rotate(1)
        elif key == K_RIGHT:
            self.items[self.selected_index].rotate(-1)
        elif key == K_UP:
            self.selected_index = (self.selected_index-1) % len(self.items)
        elif key == K_DOWN:
            self.selected_index = (self.selected_index+1) % len(self.items)
        else:
            StateWindow.handle_keypress(self, key)
        
    def render(self, screen):
        screen.fill((0, 0, 0))
        item_height = min(60, self.get_height()/(len(self.items) + 5))
        total_menu_height = item_height * len(self.items)
        top_item_offset = (self.get_height() - total_menu_height) / 2
        
        # TODO: Render title on top and bottom_hint at bottom
        
        for idx, item in enumerate(self.items):
            y_offset = top_item_offset + idx * item_height
            
            if idx == self.selected_index:
                screen.fill((150, 150, 150), 
                            rect=pygame.Rect(0, y_offset, self.get_width(), item_height)) 

            text_img = self.font.render(item.text, 1, self.font_color)
            text_pos = text_img.get_rect()
            text_pos.centerx = self.get_rect().centerx
            text_pos.centery = y_offset + item_height / 2
            screen.blit(text_img, text_pos)    

class GatewayWindow(MenuWindow):
    """
    Gateway Windows function like a usual MenuWindow, but
    there is only one changeable item. Depending on what is 
    selected there, the successor varies accordingly.
    """
    
    def __init__(self, dimensions):
        MenuWindow.__init__(self, dimensions)
        self.gateway_mapping = {}
        
    def set_successor(self, succ, idx):
        succ.predecessor = self
        self.gateway_mapping[idx] = succ

    def get_successor(self):
        idx = self.items[0].selected_index
        return self.gateway_mapping[idx]

class InputWindow(StateWindow):
    ARBITRARY = 0
    NUMERIC = 1
    CHARACTER = 2
    ALPHANUMERIC = 3
    
    # Mapping from constants above to allowed keys
    # 1: K_0 to K_9 => numbers 48 to 57
    # 2: K_a to K_z => numbers from 97 to 122
    # 3: The union of options 1 and 2
    KEY_ALLOWED = {1: range(48, 58),
                   2: range(97, 123),
                   3: range(48, 58) + range(97, 123)}

    
    def __init__(self, dimensions, text, key, type, maxlen):
        StateWindow.__init__(self, dimensions)
        self.text = text
        self.key = key 
        self.value = ''
        self.maxlen = maxlen
        self.allowed_keys = self.KEY_ALLOWED[type]
    
    def as_dict(self):
        return {self.key: self.value}
        
    def render(self, screen):
        screen.fill((0, 0, 0))
        
        # Render text
        text_img = self.font.render(self.text, 1, self.font_color)
        text_pos = text_img.get_rect()
        text_pos.centerx = self.get_rect().centerx
        text_pos.centery = self.get_height()/3
        screen.blit(text_img, text_pos)    
        
        # Render current input value
        value_img = self.font.render(self.value, 1, self.font_color)
        value_pos = value_img.get_rect()
        value_pos.centerx = self.get_rect().centerx
        value_pos.centery = self.get_height()/3 + 50
        screen.blit(value_img, value_pos)

    def handle_keypress(self, key):
        if key in self.allowed_keys:
            if len(self.value) < self.maxlen:
                self.value += chr(key)
        elif key == K_BACKSPACE:
            self.value = self.value[:-1]
        elif key == K_RETURN:
            self.finished = True
        else:
            StateWindow.handle_keypress(self, key)
      
if __name__ == '__main__':
    import sys
    pygame.init()
    
    dimensions = (450, 600)
    main_screen = pygame.display.set_mode(dimensions)
    
    clock = pygame.time.Clock()
    
    start = GatewayWindow(dimensions)
    start.add_items(MenuItem('option1', (('first', 'My First Item'),
                                        ('second', 'My Second Item'))))
                   
    win2 = InputWindow(dimensions, 
                       'Gimme something:', 
                       'sth', 
                       InputWindow.ALPHANUMERIC, 
                       15)
    
    win3 = MenuWindow(dimensions)
    win3.add_items(MenuItem('option3', (('third', 'HAHA My First Item'),
                                        ('fourth', 'HOHO My Second Item'))),
                    MenuItem('option4', (('fifth', 'HEHE My bla Item'),
                                         ('sixth', 'HIHI My other bla Item'))))
    
    win4 = MenuWindow(dimensions)
    win4.add_items(MenuItem('option5', (('hrmpf', 'HAHA'),
                                        ('gnagna', 'HOHO'))),
                    MenuItem('option6', (('blabla', 'HEHE'),
                                         ('blabla', 'HIHI'))))
                   
    start.set_successor(win2, 0) 
    start.set_successor(win3, 1)    
    win2.set_successor(win4)    

    currentWindow = start
    while currentWindow:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                currentWindow.handle_keypress(event.key)
            elif event.type == pygame.KEYUP:
                currentWindow.handle_keyrelease(event.key)
        
        currentWindow.render(main_screen)
        pygame.display.update()
        
        passed_time = clock.tick(30)
        currentWindow.proceed(passed_time)

        if currentWindow.finished:
            currentWindow.finished = False
            currentWindow = currentWindow.get_successor()
        elif currentWindow.aborted:
            currentWindow.aborted = False
            currentWindow = currentWindow.predecessor
    
    print "Total config is: %s" % start.collect_dicts()
    
    
    
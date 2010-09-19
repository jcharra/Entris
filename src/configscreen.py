import sys
import pygame

from pygame.locals import K_RETURN, K_DOWN, K_UP, K_ESCAPE, K_BACKSPACE

MENU_ITEM_HEIGHT = 50

class MenuItem(pygame.Surface):
    def __init__(self, name, values_dict=None):
        self.dimensions = (400, MENU_ITEM_HEIGHT)
        pygame.Surface.__init__(self, self.dimensions, pygame.SRCALPHA)
        
        self.name = name
        self.values_dict = values_dict
        self.values = self.values_dict and sorted(self.values_dict.keys(), 
                                                  key=lambda x: self.values_dict[x])
        self.current_index = 0
    
    def increment_index(self):
        if not self.values:
            return
        self.current_index = (self.current_index + 1) % len(self.values)
        
    def get(self):
        if self.values:
            return self.values_dict[self.values[self.current_index]]
        
    def activate(self):
        self.increment_index()
        
    def render(self):
        self.fill((0, 0, 0, 1))
        
        text = self.name
        if self.values_dict:
            text += " : %s" % self.values[self.current_index]
        
        font = pygame.font.Font(None, 24)
        text_img = font.render(text, 1, (0, 200, 0))
        text_pos = text_img.get_rect()
        text_pos.centerx = self.get_rect().centerx
        text_pos.centery = self.get_rect().centery
        self.blit(text_img, text_pos)

class ConfigScreen(pygame.Surface):
    START_ITEM = MenuItem("Start")
    
    SPEED = MenuItem("Initial speed", dict(zip(range(1, 11), range(500, 249, -25))))
    
    SCREEN_SIZE_SELECTION = MenuItem("Resolution",
                                     {"300 x 400": (300, 400), 
                                      "450 x 600": (450, 600), 
                                      "600 x 800": (600, 800)})
    
    GAME_SIZE_SELECTION = MenuItem("Game grid size",
                                   {"15 x 20": (15, 20), 
                                    "20 x 27": (20, 27),
                                    "25 x 33": (25, 33), 
                                    "30 x 40": (30, 40)})
    
    DUCK_PROBABILITY_SELECTION = MenuItem("Duck probability", dict([("%i%%" % i, float(i)/100) 
                                                                    for i in range(11)]))
    
    NEW_GAME_SELECTION = MenuItem("Game type", {"Single player": "single", 
                                                "Create online game": "create", 
                                                "Join online game": "join"})
    
    MENU_ITEMS = [GAME_SIZE_SELECTION, 
                  SCREEN_SIZE_SELECTION, 
                  SPEED,
                  DUCK_PROBABILITY_SELECTION,
                  NEW_GAME_SELECTION,
                  START_ITEM]
                       
    def __init__(self, width):
        height = len(self.MENU_ITEMS) * MENU_ITEM_HEIGHT
        pygame.Surface.__init__(self, (width, height))
        self.selected_index = 3
        self.finished = False
    
    def handle_keypress(self, key):
        if key == K_RETURN:
            self.activate_current_item()
        elif key == K_DOWN:
            self.selected_index = (self.selected_index + 1) % len(self.MENU_ITEMS)
        elif key == K_UP:
            self.selected_index = (self.selected_index - 1) % len(self.MENU_ITEMS)
    
    def activate_current_item(self):
        selected = self.MENU_ITEMS[self.selected_index]
        if selected == self.START_ITEM:
            self.finished = True
            return
        
        selected.activate()
    
    def as_dict(self):
        d = {}
        d['speed'] = self.SPEED.get()
        d['screen_size'] = self.SCREEN_SIZE_SELECTION.get()
        d['game_size'] = self.GAME_SIZE_SELECTION.get()
        d['duck_prob'] = self.DUCK_PROBABILITY_SELECTION.get()
        d['game_type'] = self.NEW_GAME_SELECTION.get()
        return d
    
    def show(self, screen):
        while not self.finished:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    sys.exit()
                    
                if event.type == pygame.KEYDOWN:
                    if event.key == K_ESCAPE:
                        sys.exit()
                    self.handle_keypress(event.key)
        
            self.render()
            config_rect = self.get_rect()
            config_rect.centery = screen.get_rect().centery
            screen.blit(self, config_rect)
            pygame.display.update()

    def render(self):
        self.fill((0, 0, 0))
        for idx, mi in enumerate(self.MENU_ITEMS):
            if idx == self.selected_index:
                fillrect = pygame.Rect(0, idx * MENU_ITEM_HEIGHT, self.get_width(), MENU_ITEM_HEIGHT)
                self.fill((50, 50, 50), fillrect)
                          
            mi_position = mi.get_rect()
            mi_position.top = idx * MENU_ITEM_HEIGHT
            mi_position.centerx = self.get_rect().centerx
            mi.render()

            self.blit(mi, mi_position)
    
    def exit(self):
        self.finished = True

class GetInputScreen(pygame.Surface):
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
    
    def __init__(self, dimensions, text, input_type=3, max_length=10, constraint=None):
        pygame.Surface.__init__(self, dimensions)
        self.text = text
        self.finished = False
        self.input = ""
        self.input_type = input_type
        self.max_length = max_length
        self.constraint = constraint
        self.allowed_keys = self.KEY_ALLOWED[input_type]
        
    def handle_keypress(self, key):
        if key == K_RETURN:
            self.finished = True
        elif key == K_ESCAPE:
            self.input = ""
            self.finished = True
        elif key in self.allowed_keys:
            self.add_input(chr(key))
        elif key == K_BACKSPACE:
            self.input = self.input[:-1]
    
    def add_input(self, char):
        if len(self.input) < self.max_length:
            self.input += char
    
    def valid_input(self):
        if not self.input:
            return False
        
        return self.constraint(self.input) if self.constraint else True
    
    def get_input(self):
        return self.input if self.valid_input() else ""
        
    def show(self, screen):
        while not self.finished:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    sys.exit()
                    
                if event.type == pygame.KEYDOWN:
                    if event.key == K_ESCAPE:
                        self.finished = True
                    self.handle_keypress(event.key)
        
            self.render()
            gs_rect = self.get_rect()
            gs_rect.centery = screen.get_rect().centery
            screen.blit(self, (0, 0))
            pygame.display.update()
    
    def render(self):
        self.fill((0, 0, 0, 1))
                
        font = pygame.font.Font(None, 24)
        text_img = font.render(self.text, 1, (0, 200, 0))
        text_pos = text_img.get_rect()
        text_pos.centerx = self.get_rect().centerx
        text_pos.centery = self.get_rect().centery - 20
        self.blit(text_img, text_pos)
        
        color = (0, 200, 0) if self.valid_input() else (200, 0, 0)
        input_img = font.render(self.input, 1, color)
        input_pos = input_img.get_rect()
        input_pos.centerx = self.get_rect().centerx
        input_pos.centery = self.get_rect().centery + 20
        self.blit(input_img, input_pos)
            
if __name__ == "__main__":
    import sys
    pygame.init()
    screen = pygame.display.set_mode((500, 350))

    cs = ConfigScreen()
    while not cs.finished:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                sys.exit()
        cs.render()
        screen.blit(cs, (0, 0))
        pygame.display.update()
    
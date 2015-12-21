import pygame

pygame.init()
from pygame.locals import *

DEFAULT_FONT = pygame.font.Font('jack_type.ttf', 18)
DEFAULT_FONT_COLOR = (0, 255, 0)
DEFAULT_HINT_COLOR = (200, 0, 0)
DEFAULT_SELECTION_BAR_COLOR = (150, 150, 150)

HEAD_GRAPHICS = None


def get_head_graphics():
    global HEAD_GRAPHICS
    if not HEAD_GRAPHICS:
        try:
            HEAD_GRAPHICS = pygame.image.load('logo.png').convert()
        except pygame.error:
            HEAD_GRAPHICS = pygame.image.load('logo.bmp').convert()

    return HEAD_GRAPHICS


class StateWindow(pygame.Surface):
    def __init__(self, dimensions):
        pygame.Surface.__init__(self, dimensions)

        self.finished = False
        self.aborted = False
        self.successor = None
        self.predecessor = None

        self.font = DEFAULT_FONT
        self.font_color = DEFAULT_FONT_COLOR
        self.hint_color = DEFAULT_HINT_COLOR
        self.selection_bar_color = DEFAULT_SELECTION_BAR_COLOR

        self.head_graphics = get_head_graphics()
        self.head_offset = self.get_width() / 2 - self.head_graphics.get_width() / 2

    def render(self, screen):
        screen.fill((0, 0, 0))
        screen.blit(self.head_graphics, (self.head_offset, 0))

    def handle_keypress(self, event):
        if event.key == K_ESCAPE:
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

    def collect_values_along_chosen_path(self):
        d = {}
        node = self
        while node:
            d.update(node.as_dict())
            node = node.get_successor()
        return d


class MenuItem(object):
    DEFAULT_SUBTITLE = """ESC: Back  ENTER: Next  ARROW KEYS: Select/Modify"""

    def __init__(self, key, value_items, subtitle=None):
        self.key = key
        self.value_items = value_items
        self.subtitle = subtitle or self.DEFAULT_SUBTITLE

        self.selected_index = 0

    def get_text(self):
        return self.value_items[self.selected_index][1]

    def get_value(self):
        return self.value_items[self.selected_index][0]

    def rotate(self, diff):
        self.selected_index = ((self.selected_index + diff)
                               % len(self.value_items))


class MenuWindow(StateWindow):
    def __init__(self, dimensions):
        StateWindow.__init__(self, dimensions)
        self.items = []
        self.title = ''
        self.selected_index = 0

    def add_items(self, *items):
        """
        Add a bunch of MenuItem instances
        """
        self.items.extend(items)

    def as_dict(self):
        return dict((item.key, item.get_value())
                    for item in self.items)

    def handle_keypress(self, event):
        key = event.key
        if key == K_RETURN:
            self.finished = True
        elif key == K_LEFT:
            self.items[self.selected_index].rotate(-1)
        elif key == K_RIGHT:
            self.items[self.selected_index].rotate(1)
        elif key == K_UP:
            self.selected_index = (self.selected_index - 1) % len(self.items)
        elif key == K_DOWN:
            self.selected_index = (self.selected_index + 1) % len(self.items)
        else:
            StateWindow.handle_keypress(self, event)

    def get_selected_item(self):
        return self.items[self.selected_index]

    def render(self, screen):
        StateWindow.render(self, screen)

        item_height = min(60, self.get_height() / (len(self.items) + 5))
        total_menu_height = item_height * len(self.items)
        top_item_offset = (self.get_height() - total_menu_height) / 2

        self.render_title(screen)
        self.render_subtitle(screen)

        for idx, item in enumerate(self.items):
            y_offset = top_item_offset + idx * item_height

            if idx == self.selected_index:
                screen.fill(self.selection_bar_color,
                            rect=pygame.Rect(0, y_offset,
                                             self.get_width(), item_height))

            text = item.get_text()
            if len(item.value_items) > 1 and idx == self.selected_index:
                # indicate changeability
                text = "<    %s    >" % text

            text_img = self.font.render(text, 1, self.font_color)
            text_pos = text_img.get_rect()
            text_pos.centerx = self.get_rect().centerx
            text_pos.centery = y_offset + item_height / 2
            screen.blit(text_img, text_pos)

    def render_title(self, screen):
        if not self.title:
            return

        title_img = self.font.render(self.title, 1, self.font_color)
        title_pos = title_img.get_rect()
        title_pos.centerx = self.get_rect().centerx
        title_pos.centery = 20
        screen.blit(title_img, title_pos)

    def render_subtitle(self, screen):
        """
        Renders a hint for the currently selected item.
        """
        if (not hasattr(self.get_selected_item(), 'subtitle')
            or not self.get_selected_item().subtitle):
            return

        subtitle_img = self.font.render(self.get_selected_item().subtitle, 1, self.hint_color)
        subtitle_pos = subtitle_img.get_rect()
        subtitle_pos.centerx = self.get_rect().centerx
        subtitle_pos.centery = self.get_height() - 40
        screen.blit(subtitle_img, subtitle_pos)


class GatewayWindow(MenuWindow):
    """
    Gateway Windows function like a usual MenuWindow, but
    there is only one selectable item. Depending on what is 
    selected, the successor varies accordingly.
    
    After instantiation, the GatewayWindow instance needs
    to be assigned successors via the set_successor function.
    """

    def __init__(self, dimensions, key):
        MenuWindow.__init__(self, dimensions)
        self.key = key

        self.selected_index = 0
        self.items = []
        self.gateway_mapping = {}

    def add_item_with_successor(self, option, caption, succ):
        # Make it a menu item without a key of its own and
        # only one option/caption pair (i.e. unchangeable).
        item = MenuItem('', ((option, caption),))
        self.items.append(item)

        # build links in pred/succ chain
        succ.predecessor = self
        self.gateway_mapping[item] = succ

    def get_successor(self):
        selected_option = self.items[self.selected_index]
        return self.gateway_mapping[selected_option]

    def as_dict(self):
        return {self.key: self.items[self.selected_index].get_value()}


class InputWindow(StateWindow):
    NUMERIC = 1
    CHARACTER = 2
    ALPHANUMERIC = 3
    HOST = 4

    # maps ints to functions expecting a unicode character
    ALLOWED_CHARS_CHECK = {1: (lambda c: c in u"0123456789"),
                           2: unicode.isalpha,
                           3: unicode.isalnum,
                           4: (lambda c: c in u"abcdefghijklmnopqrstuvwxyz1234567890.-:")}

    def __init__(self, dimensions, text, key, type, maxlen):
        StateWindow.__init__(self, dimensions)
        self.text = text
        self.key = key
        self.value = ''
        self.maxlen = maxlen
        self.allowed_chars_check = self.ALLOWED_CHARS_CHECK[type]

    def as_dict(self):
        return {self.key: self.value}

    def render(self, screen):
        StateWindow.render(self, screen)

        # Render text
        text_img = self.font.render(self.text, 1, self.hint_color)
        text_pos = text_img.get_rect()
        text_pos.centerx = self.get_rect().centerx
        text_pos.centery = self.get_height() / 3
        screen.blit(text_img, text_pos)

        # Render current input value
        value_img = self.font.render(self.value, 1, self.font_color)
        value_pos = value_img.get_rect()
        value_pos.centerx = self.get_rect().centerx
        value_pos.centery = self.get_height() / 3 + 50
        screen.blit(value_img, value_pos)

    def handle_keypress(self, event):
        key = event.key

        if key == K_BACKSPACE:
            self.value = self.value[:-1]
        elif key == K_RETURN:
            self.finished = True
        elif self.allowed_chars_check(event.unicode):
            if len(self.value) < self.maxlen:
                self.value += event.unicode

        else:
            StateWindow.handle_keypress(self, event)


if __name__ == '__main__':
    import sys

    pygame.init()

    dimensions = (450, 600)
    main_screen = pygame.display.set_mode(dimensions)

    clock = pygame.time.Clock()

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

    start = GatewayWindow(dimensions, 'XOR_option')
    start.add_item_with_successor('option1', 'First XOR Option', win2)
    start.add_item_with_successor('option2', 'Second XOR Option', win3)

    win2.set_successor(win4)

    currentWindow = start
    while currentWindow:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            if event.type == pygame.KEYDOWN:
                currentWindow.handle_keypress(event)
            elif event.type == pygame.KEYUP:
                currentWindow.handle_keyrelease(event)

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

    print "Total config is: %s" % start.collect_values_along_chosen_path()

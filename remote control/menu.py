from time import sleep
from ev3dev2.display import Display
from ev3dev2.button import Button

class Rect:
    def __init__(self, x, y, w, h):
        self.x = x; self.y = y
        self.w = w; self.h = h
        self.pos = [self.x, self.y]
        self.size = [self.w, self.h]

    def __getitem__(self, s: slice) -> list:
        return [self.x, self.y, self.w, self.h]

class DisplayButton:
    def __init__(self, label, command, pos, display: Display=None):
        self.label = label
        self.command = command
        self.pos = list(pos)
        self.size = (50, 50)
        self.display_surface = display

    def update(self, fill=False):
        self.display_surface.draw.rectangle(xy=(self.pos[0], self.pos[1], self.pos[0]+self.size[0], self.pos[1]+self.size[1]), fill="white black".split()[bool(fill)])
        text_pos = [
            self.pos[0] + self.size[0]//2 - int(len(self.label) / 2 * 6),
            self.pos[1] + self.size[1]//2 - 6
        ]
        self.display_surface.draw.text(text=self.label, xy=text_pos, fill="black white".split()[bool(fill)], align="center")

class Menu:
    def __init__(self, size):
        self.screen = Display()
        self.controls = Button()

        self.size = size
        self.buttons = []
        self.button_size = (self.screen.xres//self.size[0], self.screen.yres//self.size[1])

        self.cursor_index = 0

        self.command = False

        self.active = True
    
    def update(self):

        if self.controls.backspace: 
            return

        # if self.controls.right: self.cursor_index += 1
        # elif self.controls.left: self.cursor_index -= 1
        
        # if self.controls.up: self.cursor_index += self.size[0]
        # if self.controls.down: self.cursor_index -= self.size[0]

        # self.cursor_index = (self.cursor_index % len(self.buttons))

        if self.controls.enter:
            self.command = not self.command
            while self.controls.enter:
                self.controls.process()
                sleep(0.01)

        # self.draw()

        # self.screen.update()

        self.controls.process()

        self.controls.wait_for_released(self.controls.buttons_pressed)

        # self.screen.clear()

        sleep(0.05)

    def draw(self):

        # self.screen.clear()

        for i, button in enumerate(self.buttons): # draw buttons
            button.update(self.cursor_index == i)

        # self.screen.update()

    def add_button(self, button: DisplayButton):
        if button.display_surface == None:
            button.display_surface = self.screen
        button.size = (self.button_size[0], self.button_size[1])
        self.buttons.append(button)

# if __name__ == "__main__":
#     menu = Menu(size=(3, 3))
#     menu.add_button(DisplayButton("Start Robot", "start"))
#     menu.add_button(DisplayButton("Kill Robot", "kill"))
#     for x in range(5):
#         menu.add_button(DisplayButton("Button " + str(x)))
    
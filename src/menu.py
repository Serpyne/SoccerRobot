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
    def __init__(self, label, command, pos):
        self.label = label
        self.command = command
        self.pos = pos
        self.rect = Rect(0, 0, 50, 50)

    def update(self, screen: Display, fill=False):
        screen.draw.rectangle(xy=self.rect.pos, fill="white black".split()[bool(fill)])

        text_pos = [
            self.rect.x + self.rect.w//2 - int(len(self.label) / 2 * 3),
            self.rect.y + self.rect.h//2 - len(self.label.split(" ")) * 6
        ]
        screen.draw.text(text=self.label, xy=text_pos, fill="black white".split()[bool(fill)], align="center")

class Menu:
    def __init__(self, size):
        self.screen = Display()
        self.controls = Button()

        self.size = size
        self.buttons  = []
        self.button_size = (self.screen.xres//self.size[0], self.screen.yres//self.size[1])

        self.cursor_index = 0

        self.command = None

        self.active = True
    
    def update(self):

        if self.controls.backspace: 
            return

        self.screen.clear()

        if self.controls.right: self.cursor_index += 1
        elif self.controls.left: self.cursor_index -= 1
        
        if self.controls.up: self.cursor_index += self.size[0]
        if self.controls.down: self.cursor_index -= self.size[0]

        self.cursor_index = (self.cursor_index % len(self.buttons))

        if self.controls.enter:
            self.command = self.buttons[self.cursor_index].command

        for i, button in enumerate(self.buttons): # draw buttons
            button.update(self.screen, self.cursor_index == i)

        self.screen.update()

        self.buttons.process()

        self.buttons.wait_for_released(self.buttons.buttons_pressed)

    def add_button(self, button: DisplayButton):
        button.rect = Rect(button.pos[0], button.pos[1], self.button_size[0], self.button_size[1])
        self.buttons.append(button)

# if __name__ == "__main__":
#     menu = Menu(size=(3, 3))
#     menu.add_button(DisplayButton("Start Robot", "start"))
#     menu.add_button(DisplayButton("Kill Robot", "kill"))
#     for x in range(5):
#         menu.add_button(DisplayButton("Button " + str(x)))
    
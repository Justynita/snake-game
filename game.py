#!python3

import random as rd
import time
import curses
from pynput import keyboard
from pynput.keyboard import Key
import socket

COLOR_GREEN = 80
COLOR_BLUE = 40
COLOR_PURPLE = 20
COLOR_RED = 10
COLOR_YELLOW = 150
COLOR_MAGENTA = 90

class coord:
    DIRECTIONS = ['left', 'right', 'up', 'down']
    DIRECTIONS_MOVES = [
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1)
    ]

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def set_xy(self, coord):
        self.x = coord.x
        self.y = coord.y

    def same(self, cd):
        if self.x == cd.x and self.y == cd.y:
            return True
        return False

class plane:
    def __init__(self, screen, x=1, y=2, width=110, height=30):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.screen = screen

    def draw(self):
        self.screen.addstr(self.y, self.x + 1, '=' * (self.width-1), curses.color_pair(COLOR_PURPLE) )
        self.screen.addstr(self.y + self.height, self.x + 1, '=' * (self.width-1), curses.color_pair(COLOR_PURPLE) )

        for i in range(self.y+1, self.y + self.height):
            self.screen.addstr(i, self.x, '|', curses.color_pair(COLOR_PURPLE))

        for i in range(self.y+1, self.y + self.height):
            self.screen.addstr(i, self.x + self.width, '|', curses.color_pair(COLOR_PURPLE))


    def does_snake_touch_bounds(self, snake):
        # get head coords
        head = snake.get_head()
        hx, hy = (head.x, head.y)

        if hx <= self.x or hx >= (self.x + self.width):
            return True
        if hy <= self.y or hy >= (self.y + self.height):
            return True

        return False

    def draw_snake(self, __snake):

        dchar = snake.SNAKE_HEAD_CHAR
        dcolor = COLOR_RED
        body_len = len(__snake.coords)
        for i in range(body_len):
            body_part_coord = __snake.coords[i]
            if i == (body_len - 1):
                dchar = snake.SNAKE_TAIL_CHAR
            self.screen.addstr(body_part_coord.y, body_part_coord.x, dchar, curses.color_pair(dcolor))
            dchar = snake.SNAKE_BODY_CHAR
            dcolor = COLOR_YELLOW

    def draw_target(self, _target):
        self.screen.addstr(_target.coords.y, _target.coords.x, target.TARGET_CHAR, curses.color_pair(COLOR_RED))

    def draw_score(self, score):
        score_str = str(score.points)
        self.screen.addstr(self.y - 1, self.x, "| SCORE: " + score_str + " |", curses.color_pair(COLOR_GREEN))
        self.screen.addstr(self.y - 2, self.x + 1, '-' * (-2 + len("| SCORE: " + score_str + " |")), curses.color_pair(COLOR_GREEN))

    def top_edge(self):
        return self.y

    def bottom_edge(self):
        return self.y + self.height

    def left_edge(self):
        return self.x

    def right_edge(self):
        return self.x + self.width

    def randomize_within_bounds(self):
        tx = rd.randint(self.left_edge()+1, self.right_edge()-1)
        ty = rd.randint(self.top_edge()+1, self.bottom_edge()-1)
        return (tx, ty)


class snake:

    SNAKE_BODY_CHAR = 'o'
    SNAKE_HEAD_CHAR = '@'
    SNAKE_TAIL_CHAR = '+'

    def __init__(self, plane):
        self.length = 6
        self.coords = []  # list of coords with head at pos 0
        self.plane = plane
        self.is_paused = True

        # default direction of the snake
        self.direction = 'right'

        # init coords
        self.init_coords(self.length)

    def get_head(self):
        return self.coords[0]

    def init_coords(self, length):
        hx = rd.randint(self.plane.left_edge()+self.length, self.plane.right_edge()-1)
        hy = rd.randint(self.plane.top_edge()+1, self.plane.bottom_edge()-1)
        self.coords.append(coord(hx, hy))

        # append rest of the body
        for i in range(self.length-1):
            self.coords.append(coord(hx - i - 1, hy))

    def move(self, direction):
        pos = coord.DIRECTIONS.index(direction)
        hx = self.coords[0].x + coord.DIRECTIONS_MOVES[pos][0]
        hy = self.coords[0].y + coord.DIRECTIONS_MOVES[pos][1]

        # body chain follow
        tmp = coord(self.coords[0].x, self.coords[0].y)

        for i in range(1, self.length):
            tmp2 = coord(self.coords[i].x, self.coords[i].y)
            self.coords[i].set_xy(tmp)
            tmp.set_xy(tmp2)

        # set new head position
        self.coords[0].x = hx
        self.coords[0].y = hy

    def touches_itself(self):
        head = self.coords[0]
        for i in range(1, self.length):
            body_cd = self.coords[i]
            if head.same(body_cd):
                return True
        return False

    def progress(self):
        if not self.is_paused:
            self.move(self.direction)

    def set_pause(self, pauz):
        self.is_paused = pauz

    def set_direction(self, d):
        if snake.are_directions_opposite(d, self.direction):
            return
        self.direction = d

    def grow(self):
        self.length += 1
        self.coords.append(coord(self.coords[-1].x, self.coords[-1].y))


    def eat_target(self, _target):
        if _target.coords.same(self.coords[0]):
            _target.generate_target()
            self.grow()
            return True
        return False

    @staticmethod
    def are_directions_opposite(d1, d2):
        opposites = [
            ('left', 'right'),
            ('up', 'down')
        ]
        if (d1, d2) in opposites or (d2, d1) in opposites:
            return True
        return False

class target:

    TARGET_CHAR = 'X'

    def __init__(self, snake, plane):
        self.coords = None
        self.snake = snake
        self.plane = plane
        self.generate_target()

    def set_coord(self, x, y):
        self.coords = coord(x, y)

    def generate_target(self):
        tx, ty = (0, 0)
        while True:
            tx, ty = self.plane.randomize_within_bounds()
            tcoords = coord(tx, ty)
            # verify target doesn't overlap with the snake body
            for i in range(self.snake.length):
                if self.snake.coords[i].same(tcoords):
                    continue
            break
        self.coords = coord(tx, ty)

class score:
    def __init__(self):
        self.points = 0

    def increment(self):
        self.points += 100


class SnakeGame:

    def __init__(self, screen):
        self.screen = screen
        self.rows, self.cols = screen.getmaxyx()
        self.STOP_GAME = False

        self.plane = plane(screen, width=self.cols-2, height=self.rows-3)
        self.snake = snake(self.plane)
        self.target = target(self.snake, self.plane)
        self.score = score()
        self.GAME_SPEED = 100

        # captue key events & set direction accordingly
        self.listener = keyboard.Listener(on_press=self.on_press)

        # intialize game, curses...
        self.init_game()

    def init_game(self):
        curses.start_color()
        curses.use_default_colors()

        for i in range(0, curses.COLORS):
            curses.init_pair(i + 1, i, -1)

    def start(self):
        game_menu = menu(self)
        choice = game_menu.show_menu()

        self.screen.clear()
        self.screen.refresh()

        if choice == 0:
            # start single player game
            self.start_sp()

        elif choice == 1:
            # do not support multiplayer yet
            exit(0)
        elif choice == 2:
            exit(0)

    # start game in single player mode
    def start_sp(self):
        self.listener.start()
        while True:
            did_snake_eat_target = self.snake.eat_target(self.target)

            if(did_snake_eat_target):
                self.score.increment()
                self.GAME_SPEED += 5

            self.plane.draw()
            self.plane.draw_snake(self.snake)
            self.plane.draw_target(self.target)
            self.plane.draw_score(self.score)

            # refresh screen
            self.screen.refresh()

            # fps scheduler
            time.sleep(10 / self.GAME_SPEED)

            self.snake.progress()

            if self.plane.does_snake_touch_bounds(self.snake) or self.snake.touches_itself() or self.STOP_GAME:
                self.screen.clear()
                self.game_over()
                break

            # curses.endwin()
            self.screen.clear()

        self.game_over()

    def on_press(self, key):
        try:
            if key==Key.up:
                self.snake.set_pause(False)
                self.snake.set_direction('up')
            elif key==Key.down:
                self.snake.set_pause(False)
                self.snake.set_direction('down')
            elif key==Key.right:
                self.snake.set_pause(False)
                self.snake.set_direction('right')
            elif key==Key.left:
                self.snake.set_pause(False)
                self.snake.set_direction('left')
            elif key==Key.space:
                self.snake.set_pause(True)
            elif key==Key.esc:
                self.stop_game()
            else:
                pass

        except AttributeError:
            pass

    def stop_game(self):
        self.STOP_GAME = True

    def game_over(self):
        self.listener.stop()
        self.screen.clear()
        self.screen.refresh()
        print('GAME OVER....')
        time.sleep(3)
        exit(0)


# game menu class
class menu:

    SP_CHOICE = "Single Player"
    MP_CHOICE = "Multi Player"
    QG_CHOICE = "Quit Game"

    CHOICES = [SP_CHOICE, MP_CHOICE, QG_CHOICE]

    def __init__(self, game):
        self.rows = game.rows
        self.cols = game.cols
        self.game = game

        self.screen = game.screen

        self.sp_choice = "> " + menu.SP_CHOICE  # choice 0
        self.mp_choice = menu.MP_CHOICE  # choice 1
        self.qg_choice = menu.QG_CHOICE  # choice 2

        self.selected_choice = 0

        self.done = False
        self.key_listener = keyboard.Listener(on_press=self.on_press)

        self.update_misc()

    def update_misc(self):
        self.choices = [self.sp_choice, self.mp_choice, self.qg_choice]

    def show_menu(self):

        self.key_listener.start()

        while True:

            if self.done:
                return self.selected_choice

            # clear screen
            self.screen.clear()

            # draw top-bottom bounds
            self.screen.addstr(1, 1, "-" * (self.cols - 3), curses.color_pair(COLOR_GREEN))
            self.screen.addstr(self.rows-1, 1, "-" * (self.cols - 3), curses.color_pair(COLOR_GREEN))

            # draw left-right bounds
            for i in range(1, self.rows - 2):
                self.screen.addstr(i+1, 0, "|", curses.color_pair(COLOR_GREEN))
                self.screen.addstr(i+1, self.cols - 2, "|", curses.color_pair(COLOR_GREEN))

            y_menu = int(self.rows / 3)
            x_menu = int(self.cols / 2.4)

            self.screen.addstr(y_menu, x_menu , self.sp_choice, curses.color_pair(COLOR_YELLOW))
            self.screen.addstr(y_menu + 4, x_menu, self.mp_choice, curses.color_pair(COLOR_YELLOW))
            self.screen.addstr(y_menu + 8, x_menu, self.qg_choice, curses.color_pair(COLOR_YELLOW))

            # refresh screen
            self.screen.refresh()

            # wait before drawing menu again
            time.sleep(0.05)

    def update_choice(self):

        self.sp_choice = menu.SP_CHOICE
        self.mp_choice = menu.MP_CHOICE
        self.qg_choice = menu.QG_CHOICE

        if self.selected_choice == 0:
            self.sp_choice = "> " + menu.SP_CHOICE
        elif self.selected_choice == 1:
            self.mp_choice = "> " + menu.MP_CHOICE
        elif self.selected_choice == 2:
            self.qg_choice = "> " + menu.QG_CHOICE

    def on_press(self, key):
        try:
            if key==Key.up:
                if self.selected_choice > 0:
                    self.selected_choice -= 1
                    self.update_choice()
            elif key==Key.down:
                if self.selected_choice < 2:
                    self.selected_choice += 1
                    self.update_choice()
            elif key==Key.enter:
                self.process_choice()
            else:
                pass
        except AttributeError:
            pass

    def process_choice(self):
        self.key_listener.stop()
        self.done = True

def main():
    screen = curses.initscr()
    game = SnakeGame(screen)
    game.start()

if __name__ == '__main__':
    main()

#!python3

import random as rd
import time
import curses
from pynput import keyboard
from pynput.keyboard import Key


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
    def __init__(self, screen, x=5, y=3, width=110, height=30):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.screen = screen

    def draw(self):
        self.screen.addstr(self.y, self.x + 1, '=' * (self.width-1))
        self.screen.addstr(self.y + self.height, self.x + 1, '=' * (self.width-1))

        for i in range(self.y+1, self.y + self.height):
            self.screen.addstr(i, self.x, '|')

        for i in range(self.y+1, self.y + self.height):
            self.screen.addstr(i, self.x + self.width, '|')


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
        for body_part_coord in __snake.coords:
            self.screen.addstr(body_part_coord.y, body_part_coord.x, snake.SNAKE_BODY_CHAR)

    def draw_target(self, _target):
        self.screen.addstr(_target.coords.y, _target.coords.x, target.TARGET_CHAR)

    def draw_score(self, score):
        score_str = str(score.points)
        self.screen.addstr(self.y - 1, self.x, "| SCORE: " + score_str + " |")
        self.screen.addstr(self.y - 2, self.x + 1, '-' * (-2 + len("| SCORE: " + score_str + " |")))

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

    SNAKE_BODY_CHAR = 'O'

    def __init__(self, plane):
        self.length = 6
        self.coords = []  # list of coords with head at pos 0
        self.plane = plane
        self.is_paused = False

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

        self.plane = plane(screen)
        self.snake = snake(self.plane)
        self.target = target(self.snake, self.plane)
        self.score = score()
        self.GAME_SPEED = 100

        # captue key events & set direction accordingly
        self.listener = keyboard.Listener(on_press=self.on_press)

    def start(self):
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

            curses.endwin()
            self.screen.clear()

            self.snake.progress()

            if self.plane.does_snake_touch_bounds(self.snake) or self.snake.touches_itself() or self.STOP_GAME:
                self.screen.clear()
                self.game_over()
                break

        self.game_over()


    def show_menu():
        pass

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
        print('GAME OVER....')
        time.sleep(3)
        curses.endwin()
        self.screen.clear()
        exit(0)

def main():
    screen = curses.initscr()
    game = SnakeGame(screen)

    game.start()

if __name__ == '__main__':
    main()

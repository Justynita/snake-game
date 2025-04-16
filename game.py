#!python3

import random as rd
import time
import curses
from pynput import keyboard
from pynput.keyboard import Key
import socket
from coord import Coord
from game_client import Client

COLOR_GREEN = 80
COLOR_BLUE = 40
COLOR_PURPLE = 20
COLOR_RED = 10
COLOR_YELLOW = 150
COLOR_MAGENTA = 90


class Plane:
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

    def erase_snake(self, __snake):
        '''replace snake with spaces'''
        for c in __snake.coords:
            self.screen.addstr(c.y, c.x, ' ')

    def draw_snake(self, __snake):
        dchar = Snake.SNAKE_HEAD_CHAR
        dcolor = COLOR_RED
        body_len = len(__snake.coords)
        for i in range(body_len):
            body_part_coord = __snake.coords[i]
            if i == (body_len - 1):
                dchar = Snake.SNAKE_TAIL_CHAR
            self.screen.addstr(body_part_coord.y, body_part_coord.x, dchar, curses.color_pair(dcolor))
            dchar = Snake.SNAKE_BODY_CHAR
            dcolor = COLOR_YELLOW

    def draw_target(self, _target):
        self.screen.addstr(_target.coords.y, _target.coords.x, Target.TARGET_CHAR, curses.color_pair(COLOR_RED))

    def erase_target(self, _target):
        self.screen.addstr(_target.coords.y, _target.coords.x, ' ')

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

    def draw_countdown(self, start_time_seconds):
        countdown_message = f'GAME STARTS IN: '
        middle_x = self.x + int(self.width/2)
        middle_y = self.y + int(self.height/2)
        msg_start_x = middle_x-int(len(countdown_message)/2)

        # draw empty message box
        for i in [-2, 2]:
            self.screen.addstr(middle_y+i, msg_start_x-2, '-'*(len(countdown_message)+5), curses.color_pair(COLOR_GREEN))
        for i in [-1, 0, 1]:
            self.screen.addstr(middle_y+i, msg_start_x-2, '|' + ' '*(len(countdown_message)+3) + '|', curses.color_pair(COLOR_GREEN))

        self.screen.refresh()
        # draw countdown message with correct time
        while True:
            current_time_seconds = int(time.strftime("%S"))
            time_left = (start_time_seconds-current_time_seconds)%60
            self.screen.addstr(middle_y, msg_start_x, countdown_message + str(time_left), curses.color_pair(COLOR_GREEN))
            self.screen.refresh()
            time.sleep(1)
            if time_left == 1:
                # replace everything with spaces
                for i in range(-2, 3):
                    self.screen.addstr(middle_y+i, msg_start_x-2, ' '*(len(countdown_message)+7))
                self.screen.refresh()
                return


class Snake:

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

    def set_coords(self, coord_list):
        self.coords = []
        for c in coord_list:
            self.coords.append(c)


    def init_coords(self, length):
        hx = rd.randint(self.plane.left_edge()+self.length, self.plane.right_edge()-1)
        hy = rd.randint(self.plane.top_edge()+1, self.plane.bottom_edge()-1)
        self.coords.append(Coord(hx, hy))

        # append rest of the body
        for i in range(self.length-1):
            self.coords.append(Coord(hx - i - 1, hy))

    def move(self, direction):
        pos = Coord.DIRECTIONS.index(direction)
        hx = self.coords[0].x + Coord.DIRECTIONS_MOVES[pos][0]
        hy = self.coords[0].y + Coord.DIRECTIONS_MOVES[pos][1]

        # body chain follow
        tmp = Coord(self.coords[0].x, self.coords[0].y)

        for i in range(1, self.length):
            tmp2 = Coord(self.coords[i].x, self.coords[i].y)
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

    def touches_enemy_snake(self, enemy_snake):
        head = self.coords[0]
        for i in range(1, enemy_snake.length):
            enemy_snake_cd = enemy_snake.coords[i]
            if head.same(enemy_snake_cd):
                return True
        return False

    def progress(self):
        if not self.is_paused:
            self.move(self.direction)

    def set_pause(self, pauz):
        self.is_paused = pauz

    def set_direction(self, d):
        if Snake.are_directions_opposite(d, self.direction):
            return
        self.direction = d

    def grow(self):
        self.length += 1
        self.coords.append(Coord(self.coords[-1].x, self.coords[-1].y))


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


class Target:

    TARGET_CHAR = 'X'

    def __init__(self, snake, plane):
        self.coords = None
        self.snake = snake
        self.plane = plane
        self.generate_target()

    def set_coords(self, x, y):
        self.coords = Coord(x, y)

    def generate_target(self):
        tx, ty = (0, 0)
        while True:
            tx, ty = self.plane.randomize_within_bounds()
            tcoords = Coord(tx, ty)
            # verify target doesn't overlap with the snake body
            for i in range(self.snake.length):
                if self.snake.coords[i].same(tcoords):
                    continue
            break
        self.coords = Coord(tx, ty)

class Score:
    def __init__(self):
        self.points = 0

    def increment(self):
        self.points += 100


class SnakeGame:

    def __init__(self, screen):
        self.screen = screen
        self.rows, self.cols = screen.getmaxyx()
        self.STOP_GAME = False

        self.plane = Plane(screen, width=self.cols-2, height=self.rows-3)
        self.snake = Snake(self.plane)
        self.target = Target(self.snake, self.plane)
        self.score = Score()
        self.GAME_SPEED = 100

        # captue key events & set direction accordingly
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.made_move = False

        # intialize game, curses...
        self.init_game()

    def init_game(self):
        curses.start_color()
        curses.use_default_colors()

        for i in range(0, 255):
            curses.init_pair(i + 1, i, -1)

    def start(self):
        game_menu = Menu(self)
        choice = game_menu.show_menu()

        self.screen.clear()
        self.screen.refresh()

        if choice == 0:
            # start single player game
            self.start_sp()

        elif choice == 1:
            # join multiplayer game
            self.start_mp()

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

        self.made_move = True


    def stop_game(self):
        self.STOP_GAME = True

    def game_over(self, result=''):
        self.listener.stop()
        self.screen.clear()
        self.screen.refresh()
        print('GAME OVER....')
        print(result)
        print(f'Your score: {self.score.points}')
        time.sleep(3)
        exit(0)

    def draw_full_screen_border(self):
        # draw top-bottom bounds
        self.screen.addstr(1, 1, "-" * (self.cols - 3), curses.color_pair(COLOR_GREEN))
        self.screen.addstr(self.rows-1, 1, "-" * (self.cols - 3), curses.color_pair(COLOR_GREEN))

        # draw left-right bounds
        for i in range(1, self.rows - 2):
            self.screen.addstr(i+1, 0, "|", curses.color_pair(COLOR_GREEN))
            self.screen.addstr(i+1, self.cols - 2, "|", curses.color_pair(COLOR_GREEN))

    def display_waiting_message(self):
        # display waiting message
        msg = "Preparing the game..."
        mid_x = int((self.cols-len(msg))/2)
        mid_y = int(self.rows/2)
        self.screen.addstr(mid_y, mid_x, msg, curses.color_pair(COLOR_GREEN))
        self.screen.refresh()


    def get_username(self):
        id_phrase = "Enter username: "
        mid_x = int((self.cols-len(id_phrase))/2)
        mid_y = int(self.rows/2)

        self.screen.addstr(mid_y, mid_x, id_phrase, curses.color_pair(COLOR_GREEN))
        self.screen.refresh()

        username = bytes.decode(self.screen.getstr(mid_y, mid_x+len(id_phrase)))
        self.screen.clear()
        self.screen.refresh()
        return username

    def start_mp(self):
        # get username from the player
        self.screen.clear()
        self.screen.refresh()
        self.screen.getstr()

        self.draw_full_screen_border()
        username = self.get_username()

        # connect to the game server
        gameClient = Client(username, "192.168.1.144", 5555)

        if not gameClient.connect():
            print("Could not connect to server.")
            exit(-1)

        # send username to the server
        while True:
            if not gameClient.identify_myself():
                msg = "Username is taken."
                self.screen.addstr(int(self.rows/2)-1, int((self.cols-len(msg))/2), msg, curses.color_pair(COLOR_GREEN))
                self.screen.refresh()
                username = self.get_username()
                gameClient.user = username
                continue
            break

        self.screen.clear()
        self.draw_full_screen_border()
        self.display_waiting_message()
        self.screen.refresh()

        if not gameClient.identify_screensize():
            exit(-1)

        gameClient.start()

        # save game info received from server
        self.rows, self.cols = gameClient.game_height, gameClient.game_width
        self.target.coords = gameClient.target_coord

        # reshape plane and initialize snakes, target
        self.plane = Plane(self.screen, width=self.cols-2, height=self.rows-3)
        self.snake.set_coords(gameClient.my_snake_coords)

        enemy_snake = Snake(self.plane)
        enemy_snake.set_coords(gameClient.enemy_snake_coords)
        snakes = [self.snake, enemy_snake]

        # start key listener and clear screen
        self.listener.start()
        time.sleep(1)
        self.screen.refresh()
        self.screen.clear()

        # draw the starting screen
        self.plane.draw()
        self.plane.draw_target(self.target)
        self.plane.draw_score(self.score)
        for _snake in snakes: self.plane.draw_snake(_snake)
        self.screen.refresh()
        self.plane.draw_countdown(gameClient.starting_time)

        # redraw snakes and target in case covered by countdown
        for _snake in snakes: self.plane.draw_snake(_snake)
        self.plane.draw_target(self.target)
        self.screen.refresh()

        while True:
            do_snakes_touch_heads = snakes[0].get_head().same(snakes[1].get_head())
            for _snake in snakes:
                if self.plane.does_snake_touch_bounds(_snake) or _snake.touches_itself() or do_snakes_touch_heads:
                    result, errno = gameClient.recv_game_result()
                    if not errno:
                        self.game_over(f'It\'s a {result}!')

                    print(f"Could not understand result message, error {errno}")

            if self.STOP_GAME:
                if not gameClient.send_quit():
                    print("Could not send quitting message")
                self.game_over()

            if self.made_move:
                if not gameClient.send_move(self.snake.direction):
                    print("Could not send move")
                    self.game_over()
                self.made_move = False

            # get my snake and enemy coords from the server
            my_coords, errno = gameClient.recv_my_coords()
            gameClient.sock.sendall(str.encode(str(errno)))
            if errno:
                print(f"Received invalid coords, error: {errno}")
                exit(-1)

            enemy_coords, errno = gameClient.recv_enemy_coords()
            gameClient.sock.sendall(str.encode(str(errno)))
            if errno:
                print("Received invalid enemy coords")
                exit(-1)

            target_coord, errno = gameClient.recv_target_coord()
            gameClient.sock.sendall(str.encode(str(errno)))
            if errno:
                print("Received invalid target coord")
                exit(-1)

            for _snake in snakes: self.plane.erase_snake(_snake)
            self.plane.erase_target(self.target)
            self.screen.refresh()

            self.target.coords = target_coord
            enemy_snake.set_coords(enemy_coords)
            self.snake.set_coords(my_coords)

            self.screen.refresh()
            for _snake in snakes: self.plane.draw_snake(_snake)
            self.plane.draw_target(self.target)

            # update score if snake ate target
            if self.target.coords.same(self.snake.coords[0]):
                self.score.increment()
                self.plane.draw_score(self.score)

            self.screen.refresh()


        self.game_over()


# game menu class
class Menu:

    SP_CHOICE = "Single Player"
    MP_CHOICE = "Multi Player"
    QG_CHOICE = "Quit Game"

    CHOICES = [SP_CHOICE, MP_CHOICE, QG_CHOICE]

    def __init__(self, game):
        self.rows = game.rows
        self.cols = game.cols
        self.game = game

        self.screen = game.screen

        self.sp_choice = "> " + Menu.SP_CHOICE  # choice 0
        self.mp_choice = Menu.MP_CHOICE  # choice 1
        self.qg_choice = Menu.QG_CHOICE  # choice 2

        self.selected_choice = 0

        self.done = False
        self.key_listener = keyboard.Listener(on_press=self.on_press)

        self.update_misc()

    def update_misc(self):
        self.choices = [self.sp_choice, self.mp_choice, self.qg_choice]

    def show_menu(self):
        self.key_listener.start()
        time.sleep(1)
        # clear screen
        self.screen.refresh()
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

        while True:
            if self.done:
                return self.selected_choice

            self.screen.addstr(y_menu, x_menu , ' '*(len(self.sp_choice) + 2), curses.color_pair(COLOR_YELLOW))
            self.screen.addstr(y_menu + 4, x_menu, ' '*(len(self.mp_choice) + 2), curses.color_pair(COLOR_YELLOW))
            self.screen.addstr(y_menu + 8, x_menu, ' '*(len(self.qg_choice) + 2), curses.color_pair(COLOR_YELLOW))

            self.screen.addstr(y_menu, x_menu , self.sp_choice, curses.color_pair(COLOR_YELLOW))
            self.screen.addstr(y_menu + 4, x_menu, self.mp_choice, curses.color_pair(COLOR_YELLOW))
            self.screen.addstr(y_menu + 8, x_menu, self.qg_choice, curses.color_pair(COLOR_YELLOW))

            self.screen.refresh()

    def update_choice(self):

        self.sp_choice = Menu.SP_CHOICE
        self.mp_choice = Menu.MP_CHOICE
        self.qg_choice = Menu.QG_CHOICE

        if self.selected_choice == 0:
            self.sp_choice = "> " + Menu.SP_CHOICE
        elif self.selected_choice == 1:
            self.mp_choice = "> " + Menu.MP_CHOICE
        elif self.selected_choice == 2:
            self.qg_choice = "> " + Menu.QG_CHOICE

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
    screen.scrollok(True)
    game = SnakeGame(screen)
    game.start()

if __name__ == '__main__':
    main()

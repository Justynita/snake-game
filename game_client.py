import socket
import time
import random as rd
import curses
from coord import Coord

class Client:
    def __init__(self, user, host, port):
        self.user = user
        self.host = host
        self.port = port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.ready = False
        self.game_height = 0
        self.game_width = 0
        self.starting_time = 0

        self.target_coord = None
        self.my_snake_coords = None
        self.enemy_snake_coords = None

        self.valid_moves = Coord.DIRECTIONS      # up, down, left, right

    def connect(self):
        try:
            self.sock.connect((self.host, self.port))
        except:
            return False

        return True

    def identify_myself(self):
        self.sock.sendall(str.encode(f"username:{self.user}"))
        buf = bytes.decode(self.sock.recv(4069))

        if buf == 'OK':
            # server received username
            return True

        if buf == 'BUSY':
            print("SERVER ROOM IS BUSY, GAME IN PROGRESS")
            return False

        print(f"Server did not like username, error: {buf}")
        return False

    def send_quit(self):
        self.sock.sendall(str.encode("quitting"))
        buf = bytes.decode(self.sock.recv(4069))
        if buf == 'OK':
            # server received quit message
            return True
        print(f"Server did not understand, error: {buf}")
        return False

    def send_move(self, move):
        if move not in self.valid_moves:
            print(f"The move: {move} is not valid")
            return False

        self.sock.sendall(str.encode(f"my_move:{move}"))
        buf = bytes.decode(self.sock.recv(4069))
        if buf == 'OK':
            # server received move
            return True

        print(f"Server did not like move {move}, error: {buf}")
        return False

    def recv_starting_time(self):
        '''will return (time, errno)'''
        msg = bytes.decode(self.sock.recv(1024))
        ln = len('time:')

        if msg[0:ln] != 'time:':
            return 0, 1

        time_str = msg[ln:]
        time_seconds = 0

        try:
            time_seconds = int(time_str)
        except:
            return 0, 2

        return time_seconds, 0

    def recv_game_result(self):
        '''will return (status, errno)'''
        valid_results = ['draw', 'win', 'loss']
        msg = bytes.decode(self.sock.recv(1024))
        ln = len('result:')

        if msg[0:ln] != 'result:':
            return '', 1

        result = msg[ln:]
        if result not in valid_results:
            return '', 2

        return result, 0

    def recv_target_coord(self):
        '''will return ((x, y), errno)'''
        msg = bytes.decode(self.sock.recv(1024))
        ln = len('target_coord:')

        if msg[0:ln] != 'target_coord:':
            return (0, 0), 1

        if (len(msg) < ln + 3) or (len(msg) > ln + 9):
            return (0, 0), 2

        comma_index = msg.find(',')
        if comma_index not in [ln+1, ln+2, ln+3, ln+4]:
            return (0, 0), 2

        x_str = msg[ln:comma_index]
        y_str = msg[comma_index+1:]

        x = 0
        y = 0
        try:
            x = int(x_str)
            y = int(y_str)
        except:
            return (0, 0), 2

        return Coord(x, y), 0

    def recv_my_coords(self):
        '''will return list of coord tuples and errno'''
        msg = bytes.decode(self.sock.recv(1024))
        ln = len('your_coords:')

        if msg[0:ln] != 'your_coords:':
            return [], 1

        if (len(msg) < ln + 5):
            return [], 2

        ''' split all coords into list of individual coord strings
            in the format '(x,y'
        '''
        coord_list = msg[ln:-1].split(')')
        received_coords = []

        # append all received coords
        for coord_string in coord_list:
            comma_index = coord_string.find(',')
            if comma_index not in [1, 2, 3, 4]:
                return [], 2

            x_str = coord_string[1:comma_index]
            y_str = coord_string[comma_index+1:]

            x = 0
            y = 0
            try:
                x = int(x_str)
                y = int(y_str)
            except:
                return [], 2

            received_coords.append(Coord(x, y))

        return received_coords, 0

    def recv_enemy_coords(self):
        '''will return list of coord tuples and errno'''
        msg = bytes.decode(self.sock.recv(1024))
        ln = len('enemy_coords:')

        if msg[0:ln] != 'enemy_coords:':
            return [], 1

        if len(msg) < ln + 5:
            return [], 2

        ''' split all coords into list of individual coord strings
            in the format '(x,y'
        '''
        coord_list = msg[ln:-1].split(')')
        received_coords = []

        # append all received coords
        for coord_string in coord_list:
            comma_index = coord_string.find(',')
            if comma_index not in [1, 2, 3, 4]:
                return [], 2

            x_str = coord_string[1:comma_index]
            y_str = coord_string[comma_index+1:]

            x = 0
            y = 0
            try:
                x = int(x_str)
                y = int(y_str)
            except:
                return [], 2

            received_coords.append(Coord(x, y))

        return received_coords, 0

    def recv_shared_screen_size(self):
        '''will return (height, width, errno)'''
        msg = bytes.decode(self.sock.recv(1024))
        ln = len('shared_screen_size:')

        if len(msg) < (ln + 5):
            return 0, 0, 1

        if msg[0:ln] != 'shared_screen_size:':
            return 0, 0, 1

        if len(msg) > (ln + 9):
            return 0, 0, 2

        x_index = msg.find('x')
        if (x_index < 0) or (x_index not in [ln+2, ln+3, ln+4]):
            return 0, 0, 2

        height_string = msg[ln:x_index]
        width_string = msg[x_index+1:]

        height = 0
        width = 0
        try:
            height = int(height_string)
            width = int(width_string)
        except:
            return 0, 0, 2

        return height, width, 0

    def identify_screensize(self):
        screen = curses.initscr()
        height, width = screen.getmaxyx()
        self.sock.sendall(str.encode(f"screen_size:{height}x{width}"))
        buf = bytes.decode(self.sock.recv(4069))

        if buf == 'OK':
            # server received Screen-Size
            self.ready = True
            return True

        print(f"Server did not like Screen-Size, error: {buf}")
        return False

    def start(self):
        if not self.ready:
            print("Client not ready")
            exit(-1)

        height, width, errno = self.recv_shared_screen_size()
        self.sock.sendall(str.encode(str(errno)))
        if errno:
            print("Received invalid shared screen-size")
            exit(-1)
        self.game_height = height
        self.game_width = width

        my_coords, errno = self.recv_my_coords()
        self.sock.sendall(str.encode(str(errno)))
        if errno:
            print("Received invalid coords")
            exit(-1)
        self.my_snake_coords = my_coords.copy()

        enemy_coords, errno = self.recv_enemy_coords()
        self.sock.sendall(str.encode(str(errno)))
        if errno:
            print("Received invalid enemy coords")
            exit(-1)
        self.enemy_snake_coords = enemy_coords.copy()

        target_coord, errno = self.recv_target_coord()
        self.sock.sendall(str.encode(str(errno)))
        if errno:
            print("Received invalid target coord")
            exit(-1)
        self.target_coord = target_coord

        time_seconds, errno = self.recv_starting_time()
        self.sock.sendall(str.encode(str(errno)))
        if errno:
            print(f"Received invalid time {errno}")
            exit(-1)
        self.starting_time = time_seconds

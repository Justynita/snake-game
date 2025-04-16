import socket
import time
from enum import Enum
import random as rd
from coord import Coord


INITIAL_SNAKE_LENGTH = 6
INITIAL_SNAKE_DIRECTION = 'right'

class PlayerStatus(Enum):
    READY = 0
    WAITING_FOR_USERNAME = 1
    WAITING_FOR_SCREEN_SIZE = 2

class Player:
    def __init__(self, sock, addr, id):
        self.sock = sock
        self.addr = addr
        self.id = id
        self.screen_height = 0
        self.screen_width = 0

        self.snake_coords = []  # list of Coord Objects
        self.snake_length = INITIAL_SNAKE_LENGTH
        self.snake_direction = INITIAL_SNAKE_DIRECTION


    def init_coords(self, head_coords):
        self.snake_coords.append(head_coords)
        hx, hy = head_coords.coords()

        # append rest of the body
        for i in range(INITIAL_SNAKE_LENGTH - 1):
            self.snake_coords.append(Coord(hx - i - 1, hy))

    def head_coords(self):
        return self.snake_coords[0]

    def width(self):
        return self.screen_width

    def height(self):
        return self.screen_height

    def overlaps(self, coord):
        for c in self.snake_coords:
            if c == coord:
                return True
        return False

    def snake_grow(self):
        self.snake_length += 1
        self.snake_coords.append(Coord(self.snake_coords[-1].x, self.snake_coords[-1].y))

    def snake_hits_something(self, enemy, width, height):
        # check if snake hits itself
        head = self.snake_coords[0]
        for i in range(1, self.snake_length):
            body_cd = self.snake_coords[i]
            if head.same(body_cd):
                return True

        # check if snake hits enemy
        if enemy.overlaps(head):
            return True

        # check if snake hits bounds
        if head.x <= 0 or head.x >= width:
            return True
        if head.y <= 1 or head.y >= height:
            return True

        return False

    def setScreenSize(self, height, width):
        self.screen_height = height
        self.screen_width = width

    def status(self):
        if self.id == "":
            return PlayerStatus.WAITING_FOR_USERNAME

        if self.screen_height == 0:
            return PlayerStatus.WAITING_FOR_SCREEN_SIZE

        return PlayerStatus.READY

    def move_snake(self):
        pos = Coord.DIRECTIONS.index(self.snake_direction)
        hx = self.snake_coords[0].x + Coord.DIRECTIONS_MOVES[pos][0]
        hy = self.snake_coords[0].y + Coord.DIRECTIONS_MOVES[pos][1]

        # body chain follow
        tmp = Coord(self.head_coords().x, self.head_coords().y)

        for i in range(1, self.snake_length):
            tmp2 = Coord(self.snake_coords[i].x, self.snake_coords[i].y)
            self.snake_coords[i].set_xy(tmp)
            tmp.set_xy(tmp2)

        # set new head position
        self.snake_coords[0].x = hx
        self.snake_coords[0].y = hy

    @staticmethod
    def is_screen_size_valid(msg):
        '''will return (height, width, errno)'''

        ln = len('screen_size:')
        print("Screen_Size Identification Phrase: " + msg)
        if len(msg) < (ln + 5):
            return 0, 0, 1

        if msg[0:ln] != 'screen_size:':
            return 0, 0, 1

        x_index = msg.find('x')
        if (x_index < 0) or (x_index not in [ln+2, ln+3, ln+4]):
            return 0, 0, 2

        if len(msg) > (ln + 9):
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


class Server:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.players = []

        # In Game properties
        self.game_started = False
        self.game_height = 0
        self.game_width = 0
        self.ready_list = []
        self.starting_time = 0
        self.last_message_time = 0
        self.target_coord = None

        self.initial_snake_length = INITIAL_SNAKE_LENGTH
        self.initial_snake_direction = INITIAL_SNAKE_DIRECTION

        self.set_my_ip()
        print(f"Server ip: {self.host}")

    def set_my_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        self.host = s.getsockname()[0]
        s.close()

    def is_username_valid(self, msg):
        '''will return the parsed (username, errno)'''
        ln = len('username:')
        print("Indetification Phrase: " + msg)
        if len(msg) < (ln + 1):
            return '', 1

        if msg[0:ln] != 'username:':
            return '', 1

        new_id = msg[ln:]
        for p in self.players:
            if p.id == new_id:
                return '', 2

        return new_id, 0

    def game_ready(self):
        return (len(self.ready_list) > 0)

    def start_game(self):
        self.game_started = True

    def relocate_target(self):
        c_players = [self.players[i] for i in self.ready_list]
        _is_target_overlapping = True

        while _is_target_overlapping:
            self.target_coord = Coord.from_rand((3, self.game_width-3), (3, self.game_height-3))
            _is_target_overlapping = False
            for p in c_players:
                if p.overlaps(self.target_coord):
                    _is_target_overlapping = True
                    break

    def generate_starting_coords(self):
        # initialize snake head coords at different rows with room for bounds
        y_coords = []
        hy = rd.randint(3, self.game_height-3)

        for i in self.ready_list:
            p = self.players[i]
            hx = rd.randint(self.initial_snake_length+3, self.game_width-3-INITIAL_SNAKE_LENGTH)

            while hy in y_coords:
                hy = rd.randint(3, self.game_height-3)
            y_coords.append(hy)

            p.init_coords(Coord(hx, hy))

    def set_game_screen_size(self):
        '''sets self.game_height, self.game_width to MIN({player sizes})'''
        self.game_height = self.players[self.ready_list[0]].height()
        self.game_width  = self.players[self.ready_list[0]].width()

        for i in self.ready_list:
            p = self.players[i]

            c_width = p.width()
            c_height = p.height()

            if c_width < self.game_width:
                self.game_width = c_width

            if c_height < self.game_height:
                self.game_height = c_height

    def do_we_have_enough_players(self):
        '''returns a list of indices (self.players) to participate in the game
            returns empty list [] otherwise
        '''
        self.ready_list = [i for i in range(0, len(self.players)) if (self.players[i].status() == PlayerStatus.READY)]

        if len(self.ready_list) < 2:
            self.ready_list = []


    def send_to_ready_players(self, msg):
        '''sends msg to all players in ready_list'''
        for i in self.ready_list:
            p = self.players[i]
            p.sock.sendall(msg)

            print(f"Sent: {bytes.decode(msg)} to Player {i}")

    def get_responses_from_players_in_list(self, p_list=[]):
        '''checks for a response from some or all players in ready_list
            returns 0 for success
            returns errno or -1 for disconnection
        '''
        if p_list == []:
            p_list = self.ready_list

        not_done_list = p_list.copy()
        while True:
            for i in not_done_list:
                p = self.players[i]
                try:
                    response = bytes.decode(p.sock.recv(1))
                except:
                    pass
                else:
                    if len(response) == 0:
                        # conn closed - drop player
                        self.players.pop(i)
                        print(f"removed player {p.addr}")
                        self.ready_list = []
                        return -1
                    if int(response):
                        print(f"Client received bad message, error {response}")
                        self.ready_list = []
                        return int(response)

                    print(f"Received 0 from Player {i}")
                    not_done_list.remove(i)

                    if len(not_done_list) < 1:
                        return 0
        return 0


    def start(self):
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.setblocking(False)
        self.sock.listen()

        while True:
            if self.game_ready():

                if not self.game_started:
                    current_time_seconds = int(time.strftime("%S"))
                    if current_time_seconds == self.starting_time:
                        self.start_game()
                        print("Starting Game!")

                if self.game_started:
                    if not self.communicate():
                        # game over -- disconnect players
                        self.ready_list.sort(reverse=True)
                        for j in self.ready_list:
                            self.players.pop(j)

                        self.ready_list = []
                        print(f"removed players")

            try:
                conn, addr = self.sock.accept()
                player = Player(conn, addr, "")
                self.players.append(player)
                print(f"Connected by {addr}")
            except:
                pass

            i = 0
            while i < len(self.players):
                # do not try to reconnect to player already matched to a game
                if self.game_ready():
                    if i in self.ready_list:
                        i = i + 1
                        continue

                p = self.players[i]
                player_status = p.status()

                try:
                    buf = bytes.decode(p.sock.recv(1024))
                except socket.error:
                    pass
                else:
                    if len(buf) == 0:
                        # conn closed - drop player
                        self.players.pop(i)
                        print(f"removed player {p.addr}")
                        continue


                    if player_status == PlayerStatus.WAITING_FOR_USERNAME:
                        # we expect username:%username%
                        if self.game_ready():
                            p.sock.sendall(str.encode('BUSY'))
                            i = i + 1
                            continue

                        username, error = self.is_username_valid(buf)

                        if error == 1:
                            p.sock.send(str.encode('INVALID ID PHRASE'))
                            self.players.pop(i)
                            print(f"removed player {p.addr}")

                        if error == 2:
                            # client should prompt user to choose a differ username
                            p.sock.send(str.encode('ID UNAVAILABLE'))
                            i = i + 1
                            continue

                        self.players[i].id = username
                        print(f"Player {i} @user: {username}")
                        p.sock.sendall(str.encode('OK'))

                    elif player_status == PlayerStatus.WAITING_FOR_SCREEN_SIZE:
                        # handle screen_size:<height>x<width>
                        # we expect username:%username%
                        if self.game_ready():
                            p.sock.sendall(str.encode('BUSY'))
                            i = i + 1
                            continue

                        height, width, error = Player.is_screen_size_valid(buf)

                        if error == 1:
                            p.sock.send(str.encode('INVALID SCREEN-SIZE PHRASE'))
                            i = i + 1
                            continue

                        if error == 2:
                            p.sock.send(str.encode('INVALID SCREEN_SIZE'))
                            i = i + 1
                            continue

                        self.players[i].setScreenSize(height, width)
                        print(f"Player {i} @ScreenSize: {height}x{width}")
                        p.sock.sendall(str.encode('OK'))

                    elif player_status == PlayerStatus.READY:
                        pass

                if not self.game_ready():
                    # check if we have enough players to start the game
                    self.do_we_have_enough_players()

                    if len(self.ready_list):
                        self.set_game_screen_size()
                        print('GAME STARTED!')
                        # send screen size to concerned players
                        msg = str.encode(f"shared_screen_size:{self.game_height}x{self.game_width}")
                        self.send_to_ready_players(msg)

                        # discard the game if received error
                        if self.get_responses_from_players_in_list() != 0:
                            continue

                        self.generate_starting_coords()
                        # send players their own coords
                        for i in self.ready_list:
                            p = self.players[i]

                            msg = "your_coords:"
                            for c in p.snake_coords:
                                msg += str(c.coords())

                            p.sock.sendall(str.encode(msg))
                            print(f"Sent {msg} to Player {i}")

                        if self.get_responses_from_players_in_list() != 0:
                            continue

                        # send enemy coords (one enemy)
                        for i in self.ready_list:
                            p = self.players[i]

                            enemy_list = self.ready_list.copy()
                            enemy_list.remove(i)
                            for j in enemy_list:
                                msg = "enemy_coords:"
                                for c in self.players[j].snake_coords:
                                    msg += str(c.coords())

                                p.sock.sendall(str.encode(msg))
                                print(f"Sent {msg} to Player {j}")

                        if self.get_responses_from_players_in_list() != 0:
                            continue

                        # position the target within bounds and send the coord to players
                        self.relocate_target()
                        msg = str.encode(f"target_coord:{self.target_coord.x},{self.target_coord.y}")
                        self.send_to_ready_players(msg)

                        if self.get_responses_from_players_in_list() != 0:
                            continue

                        print("All coords received successfully")

                        current_time_seconds = int(time.strftime("%S"))
                        self.starting_time = (current_time_seconds + 6)%59
                        # send starting time to ready players
                        msg = str.encode(f"time:{str(self.starting_time)}")
                        self.send_to_ready_players(msg)
                        if self.get_responses_from_players_in_list() != 0:
                            continue

                        self.last_message_time = round(time.time() * 1000)

                i = i + 1

            time.sleep(0.02)

    def communicate(self):
        valid_moves = ['up', 'down', 'left', 'right']
        participating_players = [self.players[i] for i in self.ready_list]



        # if snake ate target, increment length & relocate target
        for p in participating_players:
            if p.overlaps(self.target_coord):
                print(f"Player {p.id} ate target")
                p.snake_grow()
                self.relocate_target()
                break

        for p in participating_players:
            print(f"checking msg from player: {p.id}")
            try:
                buf = bytes.decode(p.sock.recv(1024))
            except:
                pass
            else:
                if len(buf) == 0:
                    # conn closed - player quit
                    p_ind = self.players.index(p)
                    self.ready_list.remove(p_ind)
                    # notify other player that enemy quit
                    msg = str.encode("enemy_quit")
                    print(f"Players left: {self.ready_list}")
                    self.send_to_ready_players(msg)
                    self.get_responses_from_players_in_list()
                    self.ready_list.append(p_ind)
                    return False


                if buf[0:len('my_move:')] == 'my_move:':
                    # extract new move
                    new_move = buf[len('my_move:'):]
                    if new_move not in valid_moves:
                        # player sent an invalid move
                        p.sock.sendall(str.encode('INVALID_MOVE'))
                        continue
                    # confirm reception of valid move
                    p.sock.sendall(str.encode('OK'))
                    print(f"received {new_move} from Player {p.id}")

                    # change snake direction
                    p.snake_direction = new_move
                    continue

                if buf[0:len('quitting')] == 'quitting':
                    print("Received quit message")
                    p.sock.sendall(str.encode('OK'))
                    # remove player
                    self.ready_list.remove(self.players.index(p))
                    # notify other player that enemy quit
                    msg = str.encode("enemy_quit")
                    self.send_to_ready_players(msg)
                    self.get_responses_from_players_in_list()
                    return False

                p.sock.sendall(str.encode(f'COMMAND {buf} IS INVALID'))

        current_time_ms = round(time.time() * 1000)

        # send new move every 0.1 seconds
        if current_time_ms - self.last_message_time >= 100:
            for p in participating_players:
                p.move_snake()

            # check for collisions
            for p in participating_players:
                enemy_list = participating_players.copy()
                enemy_list.remove(p)
                for enemy in enemy_list:
                    if p.head_coords() == enemy.head_coords():
                        # head-head = draw
                        print("It's a draw!")
                        self.send_to_ready_players(str.encode("result:draw"))
                        self.get_responses_from_players_in_list()
                        return False

                    if p.snake_hits_something(enemy, self.game_width, self.game_height):
                        # player p loses, enemy wins
                        print("Snake collision")
                        p.sock.sendall(str.encode("result:loss"))
                        enemy.sock.sendall(str.encode("result:win"))
                        self.get_responses_from_players_in_list()
                        return False

            # send new snake coords to players
            for p in participating_players:
                msg = "your_coords:"
                for c in p.snake_coords:
                    msg += str(c.coords())

                p.sock.sendall(str.encode(msg))
                print(f"Sent {msg} to Player {p.id}")
            if self.get_responses_from_players_in_list() != 0:
                return False

            print("sent snakes their coords")

            # send enemy coords (one enemy)
            for p in participating_players:
                enemy_list = participating_players.copy()
                enemy_list.remove(p)
                for enemy in enemy_list:
                    msg = "enemy_coords:"
                    for c in enemy.snake_coords:
                        msg += str(c.coords())

                    p.sock.sendall(str.encode(msg))
                    print(f"Sent {msg} to Player {enemy.id}")
            if self.get_responses_from_players_in_list() != 0:
                return False

            # send target coord to players
            msg = str.encode(f"target_coord:{self.target_coord.x},{self.target_coord.y}")
            self.send_to_ready_players(msg)

            if self.get_responses_from_players_in_list() != 0:
                print("did not get responses")
                return False

            print('end of comm loop\n\n')
            self.last_message_time = round(time.time() * 1000)

        return True


gameServer = Server("127.0.0.1", 5555)
gameServer.start()

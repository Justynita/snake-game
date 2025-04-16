import random as rd

class Coord:
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

    def coords(self):
        return (self.x, self.y)

    def set_xy(self, coord):
        self.x = coord.x
        self.y = coord.y

    def same(self, cd):
        if self.x == cd.x and self.y == cd.y:
            return True
        return False

    def __eq__(self, other):
        return ((self.x == other.x) and (self.y == other.y))

    @staticmethod
    def from_rand(x_space, y_space):
        ''' x_space: tuple of (x1, x2)
            y_space: tuple of (y1, y2)
        '''
        x1, x2 = x_space
        y1, y2 = y_space
        x = rd.randint(x1, x2)
        y = rd.randint(y1, y2)

        return Coord(x, y)

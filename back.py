from dataclasses import dataclass
from enum import Enum, auto


@dataclass
class Vector2:
    x: int = 0
    y: int = 0

    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)

    def __mul__(self, num):
        return Vector2(self.x * num, self.y * num)

    def __div__(self, num):
        return self * (1/num)


class Move(Vector2, Enum):
    LEFT      = Vector2(-1, 0)
    DOWNLEFT  = Vector2(-1, 1)
    DOWN      = Vector2(0, 1)
    DOWNRIGHT = Vector2(1, 1)
    RIGHT     = Vector2(1, 0)
    UPRIGHT   = Vector2(1, -1)
    UP        = Vector2(0, -1)
    UPLEFT    = Vector2(-1, -1)


class Game:
    def __init__(self, sizex=7, sizey=7, players=2):
        if players not in (2, 4):
            raise ValueError('Game supports only 2 and 4 players')
        if players == 4:
            if sizex != sizey or sizex % 2 != 1:
                raise ValueError('The field must be square with an odd sized side')
        else:
            if sizex % 2 != 1 or sizey % 2 != 1:
                raise ValueError('The field must have odd sized sides')
        self.sizex = sizex
        self.sizey = sizey
        self.size = Vector2(sizex, sizey)
        self.ball_position = Vector2(sizex//2, sizey//2)
        self.players = players

    def move(self, move: Move):
        new_ball_position : Vector2 = self.ball_position + move.value
        if new_ball_position.x < 0 or new_ball_position.x >= self.sizex:
            raise RuntimeError('This move is illegal')
        if new_ball_position.y < 0 or new_ball_position.y >= self.sizey:
            raise RuntimeError('This move is illegal')

        self.ball_position = new_ball_position

    def check_win(self):
        if self.ball_position == Vector2(self.sizex//2, 0):
            return 1
        if self.ball_position == Vector2(self.sizex//2, self.sizey-1):
            return 2


if __name__ == '__main__':
    game = Game(5, 5)
    while True:
        move = Move[input().upper()]
        game.move(move)
        print(game.ball_position)
        print(game.check_win())

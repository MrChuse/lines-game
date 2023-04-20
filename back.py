from collections import defaultdict
from dataclasses import dataclass
from enum import Enum, auto


@dataclass(frozen=True)
class Vector2:
    x: int = 0
    y: int = 0

    def __str__(self) -> str:
        return f'(x: {self.x}, y: {self.y})'

    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)

    def __mul__(self, num):
        return Vector2(self.x * num, self.y * num)

    def __floordiv__(self, num):
        return Vector2(self.x // num, self.y // num)

    def __neg__(self):
        return Vector2(-self.x, -self.y)

    def __getitem__(self, index):
        if index == 0:
            return self.x
        if index == 1:
            return self.y
        raise IndexError('Vector2 index out of range')


class Move(Enum):
    UPLEFT    = Vector2(-1, -1)
    UP        = Vector2(0, -1)
    UPRIGHT   = Vector2(1, -1)
    LEFT      = Vector2(-1, 0)
    RIGHT     = Vector2(1, 0)
    DOWNLEFT  = Vector2(-1, 1)
    DOWN      = Vector2(0, 1)
    DOWNRIGHT = Vector2(1, 1)

    def inverse(self):
        return Move(-self.value)


class Game:
    def __init__(self, sizex=7, sizey=7, total_players=2):
        if total_players not in (2, 4):
            raise ValueError('Game supports only 2 and 4 players')
        if total_players == 4:
            if sizex != sizey or sizex % 2 != 1:
                raise ValueError('The field must be square with an odd sized side')
        else:
            if sizex % 2 != 1 or sizey % 2 != 1:
                raise ValueError('The field must have odd sized sides')
        self.sizex = sizex
        self.sizey = sizey
        self.size = Vector2(sizex, sizey)
        self.ball_position = self.size // 2
        self.current_player = 0
        self.total_players = total_players
        self.visited = defaultdict(list)

    def check_move(self, move: Move):
        new_ball_position : Vector2 = self.ball_position + move.value
        if new_ball_position.x < 0 or new_ball_position.x >= self.sizex:
            raise RuntimeError('This move is out of bounds')
        if new_ball_position.y < 0 or new_ball_position.y >= self.sizey:
            raise RuntimeError('This move is out of bounds')
        if move in self.visited[self.ball_position]:
            raise RuntimeError('This move was already made')

    def get_possible_moves(self):
        possible_moves = {move: True for move in Move}
        for move in Move:
            try:
                self.check_move(move)
            except RuntimeError:
                possible_moves[move] = False
        return possible_moves

    def move(self, move: Move):
        new_ball_position : Vector2 = self.ball_position + move.value
        self.check_move(move)

        # if the ball lands on a visited cell, the current player makes a second move, current player isn't changed
        if new_ball_position not in self.visited: # current player changes when ball lands on an unvisited cell
            self.current_player = (self.current_player + 1) % self.total_players

        self.visited[self.ball_position].append(move)
        self.visited[new_ball_position].append(move.inverse())
        self.ball_position = new_ball_position

    def check_win(self):
        if self.ball_position == Vector2(self.sizex//2, 0):
            return 0
        if self.ball_position == Vector2(self.sizex//2, self.sizey-1):
            return 1
        if self.total_players == 4:
            if self.ball_position == Vector2(0, self.sizey//2):
                return 2
            if self.ball_position == Vector2(self.sizex-1, self.sizey//2):
                return 3


if __name__ == '__main__':
    game = Game(5, 5)
    while True:
        move = Move[input().upper()]
        game.move(move)
        print(game.ball_position)
        print(game.get_possible_moves())
        print(game.check_win())

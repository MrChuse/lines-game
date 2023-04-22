from collections import defaultdict
from typing import Dict

import telebot
from PIL import Image, ImageDraw
from telebot import types

from back import Game, Move

with open('api_token.txt', 'r') as f:
    API_TOKEN = f.read()

bot = telebot.TeleBot(API_TOKEN)

# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message, """\
Hi there, I am LittleLinesGameBot.
Lines Game is a small multiplayer game with easy-to-learn-hard-to-master mechanics and has deep gameplay.
To see the rules, use /rules
To start a local game, use /local
To start an online game, use /online\
""")


# TODO: split this up, provide pictures
@bot.message_handler(commands=['rules'])
def print_rules(message):
    bot.reply_to(message, """\
This is similar to turn-based football on a grid.
Grid consists of _vertices_ and _edges_ which connect them.
At the start of the game the ball is located in the center of the field.
Objective of the the game is to score a goal by moving the ball to your opponent's _goal vertex_.
On their turn, a player must move the ball to the adjacent vertex, so there are 8 possible moves.
However, when the ball passes an _already visited vertex_, the player must make an _additional move_, giving him an opportunity to send the ball closer to their opponent's goal vertex.
Also, the ball leaves a trace and making a move which is a part of a trace is illegal. Crossing the trace is ok though.
""", parse_mode='markdown')

def calc_center_of_vertex(imsizex, imsizey, circle_sizex, circle_sizey, gamesizex, gamesizey, i, j):
    offsetx = (imsizex - circle_sizex) / (gamesizex - 1)
    offsety = (imsizey - circle_sizey) / (gamesizey - 1)
    return (
        i * offsetx + circle_sizex/2,
        j * offsety + circle_sizey/2
    )

def draw_grid(game: Game, im: Image.Image, draw: ImageDraw.ImageDraw):
    imsizex, imsizey = im.size

    sizex = 10
    sizey = 10

    for i in range(game.sizex):
        for j in range(game.sizey):
            centerx, centery = calc_center_of_vertex(imsizex, imsizey, sizex, sizey, game.sizex, game.sizey, i, j)
            draw.ellipse((centerx - sizex/2,
                          centery - sizex/2,
                          centerx + sizex/2,
                          centery + sizey/2),
                         fill=(255, 255, 255))

PLAYER_COLORS = {
    0: (255, 0, 0),
    1: (0, 127, 255),
    2: (63, 255, 63),
    3: (255, 127, 0)
}
def draw_moves(game: Game, im: Image.Image, draw: ImageDraw.ImageDraw):
    imsizex, imsizey = im.size

    sizex = 10
    sizey = 10

    for playermove in game.move_history:
        centerx1, centery1 = calc_center_of_vertex(imsizex, imsizey, sizex, sizey, game.sizex, game.sizey, *playermove.from_position)
        centerx2, centery2 = calc_center_of_vertex(imsizex, imsizey, sizex, sizey, game.sizex, game.sizey, *playermove.to_position)
        draw.line((centerx1, centery1, centerx2, centery2), fill=PLAYER_COLORS[playermove.player], width=5)


def send_game_state(chat_id, game: Game):
    im = Image.new('RGB', (300, 300), (51, 57, 63))
    draw = ImageDraw.Draw(im)
    draw_grid(game, im, draw)
    draw_moves(game, im, draw)

    return bot.send_photo(chat_id, im, f'Ball position: {game.ball_position}\nCurrent player: {game.current_player+1}')

arrow_symbols = '↖⬆↗⬅➡↙⬇↘'
def send_moves_keyboard(chat_id, game: Game):
    possible_moves = game.get_possible_moves()
    symbols = [symbol if possible else '❌' for symbol, possible in zip(arrow_symbols, possible_moves.values())]
    symbols.insert(4, '❌')

    kb = types.ReplyKeyboardMarkup(resize_keyboard=False, row_width=3)
    buttons = [types.KeyboardButton(symbol) for symbol in symbols]
    kb.add(*buttons, types.KeyboardButton('🏳️Resign🏳️'))
    return bot.send_message(chat_id, 'Your move:', reply_markup=kb)

local_games_params = defaultdict(dict)
local_games : Dict[int, Game] = {}

@bot.message_handler(commands=['local'])
def create_local_game(message: types.Message):
    global local_games_params
    local_games_params[message.from_user.id].update(is_local=True)
    print(local_games_params)
    create_game(message)

def create_game(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [types.KeyboardButton(symbol) for symbol in '24']
    kb.add(*buttons)
    sent = bot.send_message(
        message.chat.id, 'Enter the number of players, 2 or 4:', reply_markup=kb)
    bot.register_next_step_handler(sent, process_number_of_players)

def process_number_of_players(message: types.Message):
    try:
        players = int(message.text)
    except Exception:
        sent = bot.send_message(
            message.chat.id, 'Enter the number of players, 2 or 4:')
        bot.register_next_step_handler(sent, process_number_of_players)
        return
    if players not in (2, 4):
        sent = bot.send_message(
            message.chat.id, 'Enter the number of players, 2 or 4:')
        bot.register_next_step_handler(sent, process_number_of_players)
        return

    global local_games_params
    local_games_params[message.from_user.id].update(total_players=players)

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    buttons = [types.KeyboardButton(symbol) for symbol in ['7 7', '9 9', '11 11']]
    kb.add(*buttons)
    sent = bot.send_message(
        message.chat.id, 'Enter a board size, two odd numbers:', reply_markup=kb)
    bot.register_next_step_handler(sent, process_field_size)

def process_field_size(message: types.Message):
    board_size = message.text.split()
    if len(board_size) != 2:
        sent = bot.send_message(
            message.chat.id, 'Provide exactly *two* numbers\nEnter a board size, two odd numbers:', parse_mode='markdown')
        bot.register_next_step_handler(sent, process_field_size)
        return
    try:
        sizex = int(board_size[0])
        sizey = int(board_size[1])
    except Exception:
        sent = bot.send_message(
            message.chat.id, 'Provide two *integers*\nEnter a board size, two odd numbers:', parse_mode='markdown')
        bot.register_next_step_handler(sent, process_field_size)
        return
    if sizex % 2 != 1 or sizey %2 != 1:
        sent = bot.send_message(
            message.chat.id, 'Board sizes must be *odd*\nEnter a board size, two odd numbers:', parse_mode='markdown')
        bot.register_next_step_handler(sent, process_field_size)
        return
    if sizex < 3 or sizex > 25 or sizey < 3 or sizey > 25:
        sent = bot.send_message(
            message.chat.id, 'Board sizes must be between 3 and 25\nEnter a board size, two odd numbers:', parse_mode='markdown')
        bot.register_next_step_handler(sent, process_field_size)
        return

    global local_games_params
    local_games_params[message.from_user.id].update(sizex=sizex, sizey=sizey)

    sent = bot.send_message(
        message.chat.id, 'We are all set, starting the game:')
    start_game(message)

def start_game(message: types.Message):
    global local_games_params
    local = local_games_params[message.from_user.id].pop('is_local')
    # local_games_params[message.from_user.id].update(total_players=2)
    # local_games_params[message.from_user.id].update(sizex=5, sizey=5)
    game = Game(**local_games_params[message.from_user.id])

    global local_games
    local_games[message.from_user.id] = game

    if local:
        send_game_state(message.chat.id, game)
        sent = send_moves_keyboard(message.chat.id, game)
        bot.register_next_step_handler(sent, process_move)
    else:
        bot.send_message(message.chat.id, "This is where you'd wait for the opponent but this is not actually implemented. Bye")

arrows_to_moves = dict(zip(arrow_symbols, Move))
def process_move(message: types.Message):
    global local_games
    game = local_games[message.from_user.id]
    if 'resign' in message.text.lower():
        send_game_state(message.chat.id, game)
        bot.send_message(message.chat.id, f'Player {game.total_players-game.current_player} won! Play again? (use /local)', reply_markup=types.ReplyKeyboardRemove())
        return
    if message.text not in arrows_to_moves:
        bot.send_message(message.chat.id, f'This is an illegal move')
        sent = send_moves_keyboard(message.chat.id, game)
        bot.register_next_step_handler(sent, process_move)
    game.move(arrows_to_moves[message.text])
    won = game.check_win()
    if won is not None:
        send_game_state(message.chat.id, game)
        bot.send_message(message.chat.id, f'Player {won+1} won! Play again? (use /local)', reply_markup=types.ReplyKeyboardRemove())
        return
    send_game_state(message.chat.id, game)
    sent = send_moves_keyboard(message.chat.id, game)
    bot.register_next_step_handler(sent, process_move)


@bot.message_handler(commands=['online'])
def online_game(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    buttons = [types.KeyboardButton(symbol) for symbol in ['Create', 'Join']]
    kb.add(*buttons)
    sent = bot.send_message(
        message.chat.id, 'Create or join?', reply_markup=kb)
    bot.register_next_step_handler(sent, create_or_join)

def create_or_join(message: types.Message):
    if message.text.lower() == 'create':
        create_online_game(message)
    elif message.text.lower() == 'join':
        join_online_game(message)

def create_online_game(message: types.Message):
    global local_games_params
    local_games_params[message.from_user.id].update(is_local=False)
    create_game(message)

def join_online_game(message):
    pass


# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(func=lambda message: True)
def fallback(message):
    bot.reply_to(message, 'Unknown command')


# game = Game(7, 7, 2)
# game.move(Move.UP)
# game.move(Move.DOWNRIGHT)
# send_game_state(1489119319, game)
bot.infinity_polling()
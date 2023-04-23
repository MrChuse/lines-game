from collections import defaultdict
from typing import Dict

import telebot
from PIL import Image, ImageDraw
from telebot import types

from back import Game, Move, Vector2

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
Grid consists of _vertices_ and _edges_ connecting them.
At the start of the game the ball is located at the center of the field.
The objective of the the game is to score a goal by moving the ball to your opponent's _goal vertex_.
During their turn, a player must move the ball to the adjacent vertex, totalling to 8 possible moves.
However, when the ball passes an _already visited vertex_, the player must make an _additional move_, giving them an opportunity to send the ball closer to their opponent's goal vertex.
Also, the ball leaves a trace and making a move which is a part of a trace is illegal. Crossing the trace is ok though.
""", parse_mode='markdown')

def calc_center_of_vertex(imsizex, imsizey, circle_sizex, circle_sizey, gamesizex, gamesizey, i, j):
    offsetx = (imsizex - circle_sizex) / (gamesizex - 1)
    offsety = (imsizey - circle_sizey) / (gamesizey - 1)
    return (
        i * offsetx + circle_sizex/2,
        j * offsety + circle_sizey/2
    )

def draw_one_vertex(game: Game, im: Image.Image, draw: ImageDraw.ImageDraw, position: Vector2, color):
    imsizex, imsizey = im.size
    sizex = 10
    sizey = 10
    centerx, centery = calc_center_of_vertex(imsizex, imsizey, sizex, sizey, game.sizex, game.sizey, *position)
    draw.ellipse((centerx - sizex/2,
                  centery - sizex/2,
                  centerx + sizex/2,
                  centery + sizey/2),
                 fill=color)

def draw_grid(game: Game, im: Image.Image, draw: ImageDraw.ImageDraw):
    for i in range(game.sizex):
        for j in range(game.sizey):
            draw_one_vertex(game, im, draw, (i, j), (255, 255, 255))

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

def draw_ball(game: Game, im: Image.Image, draw: ImageDraw.ImageDraw):
    draw_one_vertex(game, im, draw, game.ball_position, PLAYER_COLORS[game.current_player])

def draw_goals(game: Game, im: Image.Image, draw: ImageDraw.ImageDraw):
    draw_one_vertex(game, im, draw, (game.sizex//2, 0), PLAYER_COLORS[0])
    draw_one_vertex(game, im, draw, (game.sizex//2, game.sizey-1), PLAYER_COLORS[1])

def send_game_state(chat_id, game: Game, remove_keyboard=False):
    im = Image.new('RGB', (300, 300), (51, 57, 63))
    draw = ImageDraw.Draw(im)
    draw_grid(game, im, draw)
    draw_moves(game, im, draw)
    draw_ball(game, im, draw)
    draw_goals(game, im, draw)

    if remove_keyboard:
        reply_markup = types.ReplyKeyboardRemove()
    else:
        reply_markup = None

    return bot.send_photo(chat_id, im, f'Ball position: {game.ball_position}\nCurrent player: {game.current_player+1}', reply_markup=reply_markup)

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
local_games : Dict[int, Game] = {} # user id -> Game
online_games : Dict[str, Dict] = defaultdict(dict) # game name -> Game, players

@bot.message_handler(commands=['local'])
def create_local_game(message: types.Message):
    global local_games_params
    local_games_params[message.from_user.id].update(is_local=True)
    create_game(message)

def create_game(message: types.Message):
    # kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    # buttons = [types.KeyboardButton(symbol) for symbol in '24']
    # kb.add(*buttons)
    # sent = bot.send_message(
    #     message.chat.id, 'Enter the number of players, 2 or 4:', reply_markup=kb)
    # bot.register_next_step_handler(sent, process_number_of_players)

    global local_games_params
    local_games_params[message.from_user.id].update(total_players=2)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    buttons = [types.KeyboardButton(symbol) for symbol in ['7 7', '9 9', '11 11']]
    kb.add(*buttons)
    sent = bot.send_message(
        message.chat.id, 'Enter a board size, two odd numbers:', reply_markup=kb)
    bot.register_next_step_handler(sent, process_field_size)

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
        sent = bot.send_message(message.chat.id, 'We are all set, starting the game:')
        send_game_state(message.chat.id, game)
        sent = send_moves_keyboard(message.chat.id, game)
        bot.register_next_step_handler(sent, process_move)
    else:
        sent = bot.send_message(message.chat.id, "Enter room name:", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(sent, process_room_name)

def process_room_name(message: types.Message):
    global online_games
    online_games[message.text].update(name=message.text, game=local_games[message.from_user.id], players=[message.from_user.id])
    sent = bot.send_message(message.chat.id, 'We are all set, starting the game and waiting for your opponent...')

arrows_to_moves = dict(zip(arrow_symbols, Move))
def parse_and_move(message: types.Message, game: Game, next_step_gandler, *args, **kwargs):
    if 'resign' in message.text.lower():
        won = game.total_players-game.current_player
        return True, won
    if message.text not in arrows_to_moves:
        bot.send_message(message.chat.id, f'This is an illegal move')
        sent = send_moves_keyboard(message.chat.id, game)
        bot.register_next_step_handler(sent, next_step_gandler, *args, **kwargs)
    game.move(arrows_to_moves[message.text])
    won = game.check_win()
    if won is not None:
        return True, won+1
    return None, None

def process_move(message: types.Message):
    global local_games
    game = local_games[message.from_user.id]

    game_ended, who_won = parse_and_move(message, game, process_move)
    if game_ended:
        send_game_state(message.chat.id, game)
        bot.send_message(message.chat.id, f'Player {who_won} won! Play again? (use /local)', reply_markup=types.ReplyKeyboardRemove())
        local_games.pop(message.from_user.id)
        return

    send_game_state(message.chat.id, game)
    sent = send_moves_keyboard(message.chat.id, game)
    bot.register_next_step_handler(sent, process_move)


@bot.message_handler(commands=['online'])
def online_game_(message: types.Message):
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

def join_online_game(message: types.Message):
    sent = bot.send_message(
        message.chat.id, 'Enter room id:', reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(sent, join_with_game_name)

def join_with_game_name(message: types.Message):
    name = message.text
    global online_games
    online_game = online_games.get(name)
    if online_game is None:
        sent = bot.send_message(
        message.chat.id, 'This room was not found\nEnter room id:')
        bot.register_next_step_handler(sent, join_with_game_name)
        return
    online_game['players'].append(message.from_user.id)
    sent = send_game_state_to_two_players(message, online_game)
    bot.register_next_step_handler(sent, process_online_move, online_game)

def send_game_state_to_two_players(message, online_game):
    players_ids = online_game['players']
    game: Game = online_game['game']
    current_player = game.current_player
    current_player_id, second_player_id = players_ids
    if current_player == 1:
        current_player_id, second_player_id = second_player_id, current_player_id

    send_game_state(second_player_id, game, remove_keyboard=True)
    send_game_state(current_player_id, game)
    sent = send_moves_keyboard(current_player_id, game)
    return sent

def process_online_move(message, online_game):
    game: Game = online_game['game']
    game_ended, who_won = parse_and_move(message, game, process_online_move, online_game)
    if game_ended:
        send_game_state(online_game['players'][0], game)
        bot.send_message(online_game['players'][0], f'Player {who_won} won! Play again? (use /online)', reply_markup=types.ReplyKeyboardRemove())
        send_game_state(online_game['players'][1], game)
        bot.send_message(online_game['players'][1], f'Player {who_won} won! Play again? (use /online)', reply_markup=types.ReplyKeyboardRemove())
        global online_games
        online_games.pop(online_game['name'])
        return
    sent = send_game_state_to_two_players(message, online_game)
    bot.register_next_step_handler(sent, process_online_move, online_game)


# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(func=lambda message: True)
def fallback(message):
    bot.reply_to(message, 'Unknown command')


# game = Game(7, 7, 2)
# game.move(Move.UP)
# game.move(Move.DOWNRIGHT)
# send_game_state(1489119319, game)
bot.infinity_polling()
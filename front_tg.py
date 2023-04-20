import telebot

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
To start the local game, use /local
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


@bot.message_handler(commands=['local'])
def create_local_game(message):
    bot.reply_to(message, """\
This is not implemented yet :(
""")


@bot.message_handler(commands=['online'])
def create_online_game(message):
    bot.reply_to(message, """\
This is not implemented yet :(
""")


# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(func=lambda message: True)
def fallback(message):
    bot.reply_to(message, 'Unknown command')


bot.infinity_polling()
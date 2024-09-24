import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import random

bot = telebot.TeleBot("BOTTOKEN")

locations = ["Пляж", "Кинотеатр", "Кафе", "Музей", "Поезд", "Самолет", "Космическая станция", "Школа"]

games = {}

#################
# START COMMAND #
#################
@bot.message_handler(commands=['start'])
def start_game(message):
    group_id = message.chat.id
    user_id = message.from_user.id
    args = message.text.split()
    # если перешёл по ссылке
    if len(args) > 1:
        group_id = int(args[1])
        # проверяем состоит ли он в группе
        try:
            member = bot.get_chat_member(group_id, user_id)
            if member.status in ['member', 'creator']:
                if user_id not in games[group_id]['players']:
                    games[group_id]['players'].append(message.from_user.id)
                    bot.send_message(user_id, "Вы присоединились к игре.")
                    bot.send_message(group_id, f"Присоединился: <a href=\"tg://user?id={user_id}\">{message.from_user.first_name}</a>", parse_mode='HTML')
                else:
                    bot.send_message(user_id, "Вы уже в игре!")
            else:
                bot.send_message(user_id, "Вы не состоите в группе в которой началась игра!")
        except Exception as e:
            print(f"Ошибка: {e}")
            return False
    # если НЕ переходил по ссылке
    else:
        # если команда отправлена в группе
        if message.chat.type == "group":
            if group_id not in games:
                games[group_id] = {
                    'players': [message.from_user.id],
                    'creator': message.from_user.id,
                    'message_id': 5,
                    'started': False
                }
                markup = InlineKeyboardMarkup()
                join_button = InlineKeyboardButton("Присоединиться к игре", url=f"https://t.me/{bot.get_me().username}?start={group_id}")
                start_game = InlineKeyboardButton("Начать игру", callback_data="start_game")
                markup.add(join_button)
                markup.add(start_game)
                line = bot.send_message(group_id, f"Игра создана! Нажмите кнопку, чтобы присоединиться.\nОрганизатор: <a href=\"tg://user?id={games[group_id]['creator']}\">{message.from_user.first_name}</a>", reply_markup=markup, parse_mode='HTML')
                games[group_id]['message_id'] = line.id
            else:
                bot.send_message(group_id, "Игра уже началась в этой группе!")
        # если команда отправлена НЕ в группе
        else:
            bot.send_message(message.chat.id, 'Привет!')

################
# START BUTTON #
################
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    if call.data == "start_game":
        if user_id == games[chat_id]['creator']:
            if len(games[chat_id]['players']) >= 3:
                game = games[chat_id]
                players = game['players']
                location = random.choice(locations)
                spy_index = random.randint(0, len(players) - 1)
                for index, player in enumerate(players):
                    if index == spy_index:
                        bot.send_message(player, "Вы шпион! Ваша задача - узнать локацию.")
                    else:
                        bot.send_message(player, f"Локация: {location}")
                game['started'] = True
                bot.send_message(chat_id, "Игра началась! Локации отправлены в ЛС.")
            else:
                bot.answer_callback_query(call.id, "Недостаточно игроков! Минимум 3.")
        else:
            bot.answer_callback_query(call.id, "Ты не организатор этой игры!")
bot.polling(none_stop=True)
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import random

bot = telebot.TeleBot("TOKEN")

locations = ["Пляж", "Кинотеатр", "Кафе", "Музей", "Поезд", "Самолет", "Космическая станция", "Школа"]

games = {}

#################
# КОМАНДА START #
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
                    'not_questioned': [],
                    'creator': message.from_user.id,
                    'current_player': None,
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
# КНОПКА START #
################
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    group_id = call.message.chat.id
    user_id = call.from_user.id
    if call.data == "start_game":
        if user_id == games[group_id]['creator']:
            if len(games[group_id]['players']) >= 1: ################# ВРЕМЕННО!!! ПОТОМ ИЗМЕНИТЬ НА 3
                players = games[group_id]['players']
                location = random.choice(locations)
                spy_index = random.randint(0, len(players) - 1)
                for index, player in enumerate(players):
                    if index == spy_index:
                        bot.send_message(player, "Вы шпион! Ваша задача - узнать локацию.")
                    else:
                        bot.send_message(player, f"Локация: {location}")
                games[group_id]['started'] = True
                games[group_id]['not_questioned'] = games[group_id]['players'][:]
                games[group_id]['current_player'] = games[group_id]['creator']
                bot.send_message(group_id, "Игра началась! Локации отправлены в ЛС.")
                send_players_list(group_id, games[group_id]['current_player'])
            else:
                bot.answer_callback_query(call.id, "Недостаточно игроков! Минимум 3.")
        else:
            bot.answer_callback_query(call.id, "Ты не организатор этой игры!")

##########################
# КНОПКА С ИМЕНЕМ ИГРОКА #
##########################
    elif int(call.data) in games[group_id]['not_questioned']:
        # проверяем что кто нажал является текущим игроком
        if user_id == games[group_id]['current_player']:
            if user_id != int(call.data):
                if user_id == games[group_id]['current_player']:
                    selected_player_id = int(call.data)
                    print(selected_player_id)
                    if selected_player_id in games[group_id]['not_questioned']:
                        # удаляем выбранного игрока из списка
                        games[group_id]['not_questioned'].remove(selected_player_id)
                        bot.send_message(group_id, f"Игрок {bot.get_chat_member(group_id, selected_player_id).user.first_name} был выбран.")
                        # усли список пуст начинаем заново
                        if not games[group_id]['not_questioned']:
                            games[group_id]['not_questioned'] = games[group_id]['players'][:]
                            bot.send_message(group_id, "Все игроки были выбраны. Начинаем новый круг.")
                        # передаем выбранному игроку право выбирать
                        games[group_id]['current_player'] = selected_player_id
                        send_players_list(group_id, games[group_id]['current_player'])
                    else:
                        bot.answer_callback_query(call.id, "Вы не можете выбрать игрока, пока вас не выбрали!")
            else:
                bot.answer_callback_query(call.id, "Нельзя выбирвать самого себя!")
        else:
            bot.answer_callback_query(call.id, "Сейчас не твоя очередь!")

############################################
# СОСТОВЛЯЕМ СПИСОК КНОПОК ИЗ ИМЁН ИГРОКОВ #
############################################
def send_players_list(group_id, current_player):
    markup = InlineKeyboardMarkup()
    for player in games[group_id]['not_questioned']:
        first_name = bot.get_chat_member(group_id, player).user.first_name
        nickname = InlineKeyboardButton(f"{first_name}", callback_data=f"{player}")
        markup.add(nickname)
    bot.send_message(group_id, f"<a href=\"tg://user?id={current_player}\">{bot.get_chat_member(group_id, current_player).user.first_name}</a> выбери игрока которого хочешь допросить:", reply_markup=markup, parse_mode='HTML')
    


bot.polling(none_stop=True)
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
    if len(args) > 1: # если перешёл по ссылке
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
    else: # если НЕ переходил по ссылке
        if message.chat.type == "group": # если команда отправлена в группе
            if group_id not in games:
                games[group_id] = {
                    'players': [message.from_user.id],
                    'not_questioned': [],
                    'selected_player_id': None,
                    'creator': message.from_user.id,
                    'current_player': None,
                    'location': None,
                    'spy_id':None,
                    'message_id': None,
                    'started': False,
                    'voting': False,
                    'votes': {}
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
        else: # если команда отправлена НЕ в группе
            bot.send_message(message.chat.id, 'Привет!')

################
# КОМАНДА NEXT #
################
@bot.message_handler(commands=['next'])
def start_game(message):
    group_id = message.chat.id
    user_id = message.from_user.id
    if message.chat.type == "group":
        if user_id == games[group_id]['current_player']: # если ввёл тот чья сейчас очередь
            games[group_id]['current_player'] = games[group_id]['selected_player_id'] # передаем выбранному игроку право выбирать
            if not games[group_id]['not_questioned']:
                bot.send_message(group_id, "Все игроки были выбраны. Начинаем голосование!")
                games[group_id]['current_player'] = 0
                games[group_id]['voting'] = True
            bot.delete_message(group_id, games[group_id]['message_id'])
            send_players_list(group_id, games[group_id]['current_player'])

################
# КНОПКА START #
################
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    group_id = call.message.chat.id
    user_id = call.from_user.id
    if call.data == "start_game":
        if user_id == games[group_id]['creator']:
            if len(games[group_id]['players']) >= 3:
                players = games[group_id]['players']
                location = random.choice(locations)
                spy_index = random.randint(0, len(players) - 1)
                for index, player in enumerate(players):
                    if index == spy_index:
                        games[group_id]['spy_id'] = games[group_id]['players'][spy_index]
                        print(games[group_id]['spy_id'])
                        bot.send_message(player, "Вы шпион! Ваша задача - узнать локацию.")
                    else:
                        bot.send_message(player, f"Локация: {location}")
                games[group_id]['started'] = True
                games[group_id]['not_questioned'] = games[group_id]['players'][:]
                games[group_id]['current_player'] = games[group_id]['creator']
                bot.send_message(group_id, "Игра началась! Локации отправлены в ЛС.")
                bot.delete_message(group_id, games[group_id]['message_id'])
                send_players_list(group_id, games[group_id]['current_player'])
            else:
                bot.answer_callback_query(call.id, "Недостаточно игроков! Минимум 3.")
        else:
            bot.answer_callback_query(call.id, "Ты не организатор этой игры!")

##########################
# КНОПКА С ИМЕНЕМ ИГРОКА #
##########################
    elif call.data in str(games[group_id]['not_questioned']):
        # проверяем что кто нажал является текущим игроком
        if user_id == games[group_id]['current_player']: # если нажал тот чья сейчас очередь
            if user_id != int(call.data): # проверяем не нажал ли он на самого себя
                selected_player_id = int(call.data)
                games[group_id]['not_questioned'].remove(selected_player_id) # удаляем выбранного игрока из списка
                bot.delete_message(group_id, games[group_id]['message_id'])
                message = bot.send_message(group_id, f"Игрок {bot.get_chat_member(group_id, games[group_id]['current_player']).user.first_name} хочет допросить {bot.get_chat_member(group_id, selected_player_id).user.first_name}.\nЗадавай свой вопрос, после принятия ответа введи команду /next")
                games[group_id]['message_id'] = message.id
                games[group_id]['selected_player_id'] = selected_player_id
            else:
                bot.answer_callback_query(call.id, "Нельзя выбирать самого себя!")
        else:
            bot.answer_callback_query(call.id, "Сейчас не твоя очередь!")

###################################
# КНОПКА С ГОЛОСОВАНИЕМ ЗА ИГРОКА #
###################################
    elif call.data in (f"vote_{player}" for player in games[group_id]['players']):
        current_player = games[group_id]['current_player']
        if user_id == games[group_id]['players'][current_player]: # если нажал тот чья сейчас очередь
            if str(f"vote_{user_id}") != call.data: # проверяем не нажал ли он на самого себя
                selected_player_id = call.data
                games[group_id]['votes'][selected_player_id] = games[group_id]['votes'].get(selected_player_id, 0) + 1
                bot.send_message(group_id, f"Голос от {bot.get_chat_member(group_id, user_id).user.first_name} принят.")
                bot.delete_message(group_id, games[group_id]['message_id'])
                games[group_id]['current_player'] += 1
                print(len(games[group_id]['players']))
                if games[group_id]['current_player'] < len(games[group_id]['players']):
                    send_players_list(group_id, games[group_id]['current_player'])
                else:
                    max_value = max(games[group_id]['votes'].values())
                    max_keys = [k for k, v in games[group_id]['votes'].items() if v == max_value]
                    if len(max_keys) >= 1:
                        if int(max_keys[0][5:]) == games[group_id]['spy_id']:
                            bot.send_message(group_id, f"Большинство проголосовали за {bot.get_chat_member(group_id, max_keys[0][5:]).user.first_name}. Он оказался шпионом! Мирные жители победили. \nВведите /start чтобы начать игру заново.")
                            del games[group_id]
                        else:
                            bot.send_message(group_id, f"Большинство проголосовали за {bot.get_chat_member(group_id, max_keys[0][5:]).user.first_name}. Он оказался порядочным жителем города!")
                            games[group_id]['players'].remove(int(max_keys[0][5:]))
                            if len(games[group_id]['players']) >= 3:
                                games[group_id]['not_questioned'] = games[group_id]['players'][:]
                                send_players_list(group_id, 0)
                            else:
                                bot.send_message(group_id, f"Мирных граждан осталось меньше 3, поздравляем шпиона под именем {bot.get_chat_member(group_id, games[group_id]['spy_id']).user.first_name} с победой! \nВведите /start чтобы начать игру заново.")
                                del games[group_id]
                    else:
                        print("Жители города не нашли общего мнения, голоса разъединились, никого не вешаем.")
            else:
                bot.answer_callback_query(call.id, "Нельзя выбирать самого себя!")
        else:
            bot.answer_callback_query(call.id, "Сейчас не твоя очередь!")

############################################
# СОСТОВЛЯЕМ СПИСОК КНОПОК ИЗ ИМЁН ИГРОКОВ #
############################################
def send_players_list(group_id, current_player):
    markup = InlineKeyboardMarkup()
    if games[group_id]['voting']:
        for player in games[group_id]['players']:
            first_name = bot.get_chat_member(group_id, player).user.first_name
            nickname = InlineKeyboardButton(f"{first_name}", callback_data=f"vote_{player}")
            markup.add(nickname)
        markup.add(InlineKeyboardButton(f"Не голосовать", callback_data=f"do_not_vote"))
        message = bot.send_message(group_id, f"<a href=\"tg://user?id={games[group_id]['players'][current_player]}\">{bot.get_chat_member(group_id, games[group_id]['players'][current_player]).user.first_name}</a> выбери игрока за которого хочешь проголосовать:", reply_markup=markup, parse_mode='HTML')
        games[group_id]['message_id'] = message.id
    else:
        for player in games[group_id]['not_questioned']:
            first_name = bot.get_chat_member(group_id, player).user.first_name
            nickname = InlineKeyboardButton(f"{first_name}", callback_data=f"{player}")
            markup.add(nickname)
        message = bot.send_message(group_id, f"<a href=\"tg://user?id={current_player}\">{bot.get_chat_member(group_id, current_player).user.first_name}</a> выбери игрока которого хочешь допросить:", reply_markup=markup, parse_mode='HTML')
        games[group_id]['message_id'] = message.id


bot.polling(none_stop=True)
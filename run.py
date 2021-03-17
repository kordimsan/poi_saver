from collections import defaultdict
import os
from flask import Flask, request
import logging
import telebot
from telebot import types
import overpy
import geocoder
api = overpy.Overpass()

from db import MongoDbContext
mongo = MongoDbContext()

TOKEN = '1648079718:AAHgjkA0pVWro3tlObdSJ3yzjSOja3Yde7I'
ADD, LOCATION, NAME, PHOTO = range(4)
bot = telebot.TeleBot(TOKEN)

CALLBACK_DATA = defaultdict(lambda: {})

def get_callback_data(chat_id):
    return CALLBACK_DATA[chat_id]

def set_callback_data(chat_id, key, value):
    CALLBACK_DATA[chat_id][key] = value

if __name__ == '__main__':

    @bot.message_handler(commands=['start'])
    def start_command(message):
        bot.send_chat_action(message.chat.id, 'typing')
        mongo.check_and_add_user(message)
        bot.send_message(message.chat.id, 'Привет, ты запустил бот который умеет сохранять твои точки интереса!')

    @bot.message_handler(commands=['add'])
    def handle_add_command(message):
        bot.send_chat_action(message.chat.id, 'typing')
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        button_geo = types.KeyboardButton(text="Отправить местоположение", request_location=True)
        keyboard.add(button_geo)
        mongo.set_state(message, LOCATION)
        bot.send_message(message.chat.id, "Нажми на кнопку и передай мне свое местоположение", reply_markup=keyboard)

    @bot.message_handler(commands=['list'])
    def handle_list_command(message):
        bot.send_chat_action(message.chat.id, 'typing')
        #bot.send_message(message.chat.id, 'Ты запустил комманду list – отображение добавленных мест!')
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        for v in mongo.get_storage(message):
            button = types.InlineKeyboardButton(
                text = v.get('name'), 
                callback_data = str(v.get('_id'))
            )
            keyboard.add(button)

        bot.send_message(message.chat.id, 'Твои сохраненные точки интереса:', reply_markup=keyboard)

    @bot.message_handler(commands=['reset'])
    def handle_reset_command(message):
        bot.send_chat_action(message.chat.id, 'typing')
        mongo.drop_storage(message)
        bot.send_message(message.chat.id, 'Ты запустил комманду reset – удалить все добавленные локации!')

    @bot.message_handler(content_types=["location"], func=lambda message: mongo.get_state(message) == LOCATION)
    def handle_message(message):
        if message.location is not None:
            bot.send_chat_action(message.chat.id, 'typing')
            set_callback_data(message.chat.id, 'current_location', str(message.location.latitude)+','+str(message.location.longitude))
            r = api.query('[out:json];node[~"^(amenity|shop)$"~"."](around:200, {},{}); out;'.format(
                message.location.latitude, message.location.longitude)
            )
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            for n in r.nodes:
                g = geocoder.osm([n.lat, n.lon], method='reverse')
                if n.tags.get('name'):
                    location = str(n.lat)+','+str(n.lon)
                    set_callback_data(message.chat.id, location, {
                        'name': n.tags.get('name'),
                        'address': g.address
                    })
                    button = types.InlineKeyboardButton(
                        text=n.tags.get('name')+'('+ g.address +')', 
                        callback_data='location_'+location
                    )
                    keyboard.add(button)

            mongo.set_state(message, NAME)
            bot.send_message(message.chat.id, 'Найдены точки интереса по близости либо введите сове название:', reply_markup=keyboard)

    @bot.message_handler(func=lambda message: mongo.get_state(message) == LOCATION)
    def handle_message(message):
        bot.send_chat_action(message.chat.id, 'typing')
        mongo.set_state(message, NAME)
        bot.send_message(message.chat.id, 'Введите название точки интереса:', reply_markup=types.ReplyKeyboardHide())

    @bot.callback_query_handler(func=lambda query: query.data[:9]=='location_')
    def callback_query(query):
        bot.send_chat_action(query.message.chat.id, 'typing')
        location =  query.data[9:]
        set_callback_data(query.message.chat.id, 'selected_location', location)
        set_callback_data(query.message.chat.id, 'name', get_callback_data(query.message.chat.id).get(location,{'name':None})['name'])
        mongo.set_state(query, PHOTO)
        bot.send_message(query.message.chat.id, 'Пришли фотографию места:', reply_markup=types.ReplyKeyboardHide())
        
    @bot.message_handler(func=lambda message: mongo.get_state(message) == NAME)
    def handle_message(message):
        bot.send_chat_action(message.chat.id, 'typing')
        set_callback_data(message.chat.id, 'selected_location', get_callback_data(message.chat.id).get('current_location'))
        set_callback_data(message.chat.id, 'name', message.text)
        mongo.set_state(message, PHOTO)
        bot.send_message(message.chat.id, 'Пришли фотографию места:', reply_markup=types.ReplyKeyboardHide())

    @bot.message_handler(content_types=["photo"], func=lambda message: mongo.get_state(message) == PHOTO)
    def handle_message(message):
        bot.send_chat_action(message.chat.id, 'typing')
        set_callback_data(message.chat.id, 'photo', message.photo[0].file_id)
        mongo.set_storage(message, get_callback_data(message.chat.id))
        mongo.set_state(message, ADD)
        bot.send_message(message.chat.id, 'Место сохранено!')

    @bot.message_handler(func=lambda message: mongo.get_state(message) == PHOTO)
    def handle_message(message):
        bot.send_chat_action(message.chat.id, 'typing')
        bot.send_message(message.chat.id, 'Ты прислал не фотографию, пришли фотографию места:')

    
    # Проверим, есть ли переменная окружения Хероку (как ее добавить смотрите ниже)
    if "HEROKU" in list(os.environ.keys()):
        logger = telebot.logger
        telebot.logger.setLevel(logging.INFO)

        server = Flask(__name__)
        @server.route('/' + TOKEN, methods=['POST'])
        def getMessage():
            bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
            return "!", 200
        @server.route("/")
        def webhook():
            bot.remove_webhook()
            bot.set_webhook(url="https://poi-saver.herokuapp.com/" + TOKEN)
            return "?", 200
        server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
    else:
        # если переменной окружения HEROKU нету, значит это запуск с машины разработчика.  
        # Удаляем вебхук на всякий случай, и запускаем с обычным поллингом.
        bot.remove_webhook()
        bot.polling(none_stop=True)
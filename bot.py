from collections import defaultdict

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
STORAGE = defaultdict(lambda: {})

def get_storage(user_id):
    return STORAGE[user_id]

def update_storage(user_id, key, value):
    STORAGE[user_id][key] = value

@bot.message_handler(commands=['start'])
def start_command(message):
    mongo.check_and_add_user(message)
    bot.send_message(message.chat.id, 'Привет, ты запустил бот который умеет сохранять твои точки интереса!')

@bot.message_handler(commands=['add'], func=lambda message: mongo.get_state(message) == ADD)
def handle_add_command(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_geo = types.KeyboardButton(text="Отправить местоположение", request_location=True)
    keyboard.add(button_geo)
    bot.send_message(message.chat.id, "Нажми на кнопку и передай мне свое местоположение", reply_markup=keyboard)
    mongo.set_state(message, LOCATION)

@bot.message_handler(content_types=["location"], func=lambda message: mongo.get_state(message) == LOCATION)
def handle_message(message):
    if message.location is not None:
        update_storage(message.chat.id, 'current_location', str(message.location.latitude)+','+str(message.location.longitude))
        r = api.query('[out:json];node[~"^(amenity|shop)$"~"."](around:200, {},{}); out;'.format(
            message.location.latitude, message.location.longitude)
        )
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        for n in r.nodes:
            g = geocoder.osm([n.lat, n.lon], method='reverse')
            if n.tags.get('name'):
                location = str(n.lat)+','+str(n.lon)
                CALLBACK_DATA[message.chat.id][location] = {
                    'name': n.tags.get('name'),
                    'address': g.address
                }
                button = types.InlineKeyboardButton(
                    text=n.tags.get('name')+'('+ g.address +')', 
                    callback_data='location_'+location
                )
                keyboard.add(button)

        bot.send_message(message.chat.id, 'Найдены точки интереса по близости либо введите сове название:', reply_markup=keyboard)
        mongo.set_state(message, NAME)

@bot.message_handler(func=lambda message: mongo.get_state(message) == LOCATION)
def handle_message(message):
    bot.send_message(message.chat.id, 'Введите название точки интереса:', reply_markup=types.ReplyKeyboardHide())
    mongo.set_state(message, NAME)

@bot.callback_query_handler(func=lambda query: query.data[:9]=='location_')
def callback_query(query):
    location =  query.data[9:]
    update_storage(query.message.chat.id, 'selected_location', location)
    update_storage(query.message.chat.id, 'name', CALLBACK_DATA[query.message.chat.id][location]['name'])
    bot.send_message(query.message.chat.id, 'Пришли фотографию места:', reply_markup=types.ReplyKeyboardHide())
    mongo.set_state(query.message, PHOTO)
    
@bot.message_handler(func=lambda message: mongo.get_state(message) == NAME)
def handle_message(message):
    update_storage(message.chat.id, 'selected_location', get_storage(message.chat.id)['current_location'])
    update_storage(message.chat.id, 'name', message.text)
    bot.send_message(message.chat.id, 'Пришли фотографию места:', reply_markup=types.ReplyKeyboardHide())
    mongo.set_state(message, PHOTO)

@bot.message_handler(content_types=["photo"], func=lambda message: mongo.get_state(message) == PHOTO)
def handle_message(message):
    update_storage(message.chat.id, 'photo', message.photo[0].file_id)
    bot.send_message(message.chat.id, 'Место сохранено!')
    mongo.set_state(message, ADD)

@bot.message_handler(func=lambda message: mongo.get_state(message) == PHOTO)
def handle_message(message):
    bot.send_message(message.chat.id, 'Ты прислал не фотографию, пришли фотографию места:')

@bot.message_handler(commands=['list'])
def handle_list_command(message):
    #bot.send_message(message.chat.id, 'Ты запустил комманду list – отображение добавленных мест!')
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for k, v in get_storage(message.chat.id).items():
        button = types.InlineKeyboardButton(
            text = k+': '+v, 
            callback_data = k
        )
        keyboard.add(button)

    bot.send_message(message.chat.id, 'Твои сохраненные точки интереса:', reply_markup=keyboard)

@bot.message_handler(commands=['reset'])
def handle_reset_command(message):
    bot.send_message(message.chat.id, 'Ты запустил комманду reset – удалить все его добавленные локации!')

bot.polling()
from collections import defaultdict

import telebot
from telebot import types
import overpy
import geocoder
api = overpy.Overpass()

TOKEN = '1648079718:AAHgjkA0pVWro3tlObdSJ3yzjSOja3Yde7I'
ADD, LOCATION, NAME, PHOTO = range(4)
bot = telebot.TeleBot(TOKEN)

USER_STATE = defaultdict(lambda: ADD)
def get_state(message):
    return USER_STATE[message.chat.id]

def update_state(message, state):
    USER_STATE[message.chat.id] = state

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, 'Привет, ты запустил бот который умеет сохранять твои точки интереса!')

@bot.message_handler(commands=['add'], func=lambda message: get_state(message) == ADD)
def handle_add_command(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_geo = types.KeyboardButton(text="Отправить местоположение", request_location=True)
    keyboard.add(button_geo)
    bot.send_message(message.chat.id, "Нажми на кнопку и передай мне свое местоположение", reply_markup=keyboard)
    update_state(message, LOCATION)

@bot.message_handler(content_types=["location"], func=lambda message: get_state(message) == LOCATION)
def handle_message(message):
    if message.location is not None:
        print(message.location)
        print("latitude: %s; longitude: %s" % (message.location.latitude, message.location.longitude))
        r = api.query('[out:json];node[~"^(amenity|shop)$"~"."](around:200, {},{}); out;'.format(message.location.latitude, message.location.longitude))
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        for n in r.nodes:
            g = geocoder.osm([n.lat, n.lon], method='reverse')
            if n.tags.get('name'):
                button = types.KeyboardButton(text=n.tags.get('name') + '('+ g.address +')')
                keyboard.add(button)
        update_state(message, NAME)

@bot.message_handler(func=lambda message: get_state(message) == LOCATION)
def handle_message(message):
        update_state(message, NAME)

@bot.callback_query_handler(func=lambda query: query.data[:9]=='location_')
def callback_query(query):
    location =  query.data[9:]
    bot.send_message(query.message.chat.id, 'Пришли фотографию места:', reply_markup=types.ReplyKeyboardHide())
    update_state(query.message, PHOTO)
    
@bot.message_handler(func=lambda message: get_state(message) == NAME)
def handle_message(message):
    bot.send_message(message.chat.id, 'Пришли фотографию места:', reply_markup=types.ReplyKeyboardHide())
    update_state(message, PHOTO)

@bot.message_handler(content_types=["photo"], func=lambda message: get_state(message) == PHOTO)
def handle_message(message):
    bot.send_message(message.chat.id, 'Место сохранено!')
    update_state(message, ADD)

@bot.message_handler(func=lambda message: get_state(message) == PHOTO)
def handle_message(message):
    bot.send_message(message.chat.id, 'Ты прислал не фотографию, пришли фотографию места:')

@bot.message_handler(commands=['list'])
def handle_list_command(message):
    bot.send_message(message.chat.id, 'Ты запустил комманду list – отображение добавленных мест!')

@bot.message_handler(commands=['reset'])
def handle_reset_command(message):
    bot.send_message(message.chat.id, 'Ты запустил комманду reset – удалить все его добавленные локации!')

bot.polling()
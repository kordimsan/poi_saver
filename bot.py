import telebot
from telebot import types
import overpy
import geocoder
api = overpy.Overpass()

TOKEN = '1648079718:AAHgjkA0pVWro3tlObdSJ3yzjSOja3Yde7I'

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, 'Привет, ты запустил бот который умеет сохранять твои точки интереса!')

@bot.message_handler(commands=['add'])
def handle_add_command(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_geo = types.KeyboardButton(text="Отправить местоположение", request_location=True)
    keyboard.add(button_geo)
    bot.send_message(message.chat.id, "Нажми на кнопку и передай мне свое местоположение", reply_markup=keyboard)

@bot.message_handler(content_types=["location"])
def handle_location(message):
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
                print(n.tags, n.lat, n.lon)
        bot.send_message(message.chat.id, 'Найдены точки интереса по близости:', reply_markup=keyboard)

@bot.message_handler(commands=['list'])
def handle_list_command(message):
    bot.send_message(message.chat.id, 'Ты запустил комманду list – отображение добавленных мест!')

@bot.message_handler(commands=['reset'])
def handle_reset_command(message):
    bot.send_message(message.chat.id, 'Ты запустил комманду reset – удалить все его добавленные локации!')

bot.polling()
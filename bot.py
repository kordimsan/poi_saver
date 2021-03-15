import telebot


TOKEN = '1648079718:AAHgjkA0pVWro3tlObdSJ3yzjSOja3Yde7I'

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, 'Привет, ты запустил бот который умеет сохранять твои точки интереса!')

@bot.message_handler(commands=['add'])
def add_command(message):
    bot.send_message(message.chat.id, 'Ты запустил комманду add – добавление нового места!')

@bot.message_handler(commands=['list'])
def list_command(message):
    bot.send_message(message.chat.id, 'Ты запустил комманду list – отображение добавленных мест!')

@bot.message_handler(commands=['reset'])
def reset_command(message):
    bot.send_message(message.chat.id, 'Ты запустил комманду reset – удалить все его добавленные локации!')

bot.polling()
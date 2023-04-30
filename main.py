import telebot
from telebot import types
from data import db_session
from data.tables import User
from random import choice, choices
import requests
from config import TOKEN


bot = telebot.TeleBot(TOKEN)
db_session.global_init('db/tables.db')
session = db_session.create_session()
button = types.KeyboardButton
n = 1


def get_user_data(user_id):
    data = session.query(User).filter(User.user_id == user_id).first()
    return {'data': data.user_id,
            'name': data.user_name,
            'balance': data.balance}


def starting_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    works_button = button('Работа')
    help_button = button('Магазин')
    balance_button = button('Баланс')
    leaders_button = button('Лидеры')
    markup.add(works_button, help_button, balance_button, leaders_button)
    return markup


@bot.message_handler(func=lambda message: message.text == "Назад в меню")
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Приветствую, я - экономический бот \n'
                                      'У меня есть много функционала, к примеру магазин, способы '
                                      'работы и прочее', reply_markup=starting_menu())
    if session.query(User).filter(User.user_id == message.from_user.id).count() == 0:
        user = User()
        user.user_name = message.from_user.first_name
        user.user_id = message.from_user.id
        session.add(user)
        session.commit()


@bot.message_handler(func=lambda message: message.text == "Работа")
def work(message):
    global button
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    casino_button = button('Казино')
    numbers_button = button('Угадай число')
    work_button = button('Перевертыши')
    menu_button = button('Назад в меню')
    markup.add(casino_button, numbers_button, work_button, menu_button)
    bot.send_message(message.chat.id, 'Выберите мини-игру', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Угадай число")
def guess_number(message):
    bot.send_message(message.chat.id, 'Угадайте число от 1 до 3')

    @bot.message_handler(content_types=['text'])
    def guessing(user_message):
        random_number = choice([1, 2, 3])
        try:
            if int(user_message.text) == random_number:
                session.query(User).filter(User.user_id == user_message.from_user.id).first().balance += 100 * n
                session.commit()
                bot.send_message(user_message.chat.id, 'Вы угадали! +100 денег', reply_markup=starting_menu())
            else:
                bot.send_message(user_message.chat.id, 'Вам не повезло', reply_markup=starting_menu())
        except ValueError:
            bot.send_message(user_message.chat.id, 'Вы ввели некорректное значение', reply_markup=starting_menu())

    bot.register_next_step_handler(message, guessing)


@bot.message_handler(func=lambda message: message.text == "Баланс")
def balance(message):
    moneys = get_user_data(message.from_user.id)['balance']
    bot.send_message(message.chat.id, f'Твой баланс: {moneys}')


@bot.message_handler(func=lambda message: message.text == "Казино")
def casino(message):
    bot.send_message(message.chat.id, 'Укажите кол-во денег, которое вы готовы поставить (Шансы 50/50)')

    @bot.message_handler(content_types=['text'])
    def guessing(user_message):
        number = choice([0, 1])
        try:
            moneys = int(user_message.text)
            not_bigger = moneys <= get_user_data(user_message.from_user.id)['balance']
            blc = session.query(User).filter(User.user_id == user_message.from_user.id).first().balance
            if number == 0 and not_bigger:
                session.query(User).filter(User.user_id == user_message.from_user.id).first().balance = blc - moneys
                session.commit()
                bot.send_message(message.chat.id, 'Вы проиграли', reply_markup=starting_menu())
            elif number == 1 and not_bigger:
                session.query(User).filter(User.user_id == user_message.from_user.id).first().balance = blc + moneys
                session.commit()
                bot.send_message(message.chat.id, 'Вы победили', reply_markup=starting_menu())
            else:
                bot.send_message(message.chat.id, 'У вас нет столько денег', reply_markup=starting_menu())
        except ValueError:
            bot.send_message(message.chat.id, 'Вы некорректно ввели ставку', reply_markup=starting_menu())

    bot.register_next_step_handler(message, guessing)


@bot.message_handler(func=lambda message: message.text == "Лидеры")
def leaders(message):
    arr = []
    for articles in session.query(User).order_by(-User.balance).limit(10):
        arr.append(f"{articles.user_name}: {articles.balance}")
    leaders_string = "\n\t".join(arr)
    bot.send_message(message.chat.id, f'Лидеры: \n  {leaders_string}', reply_markup=starting_menu())


@bot.message_handler(func=lambda message: message.text == "Коты")
def cats(message):
    if session.query(User).filter(User.user_id == message.from_user.id).first().balance >= 10:
        session.query(User).filter(User.user_id == message.from_user.id).first().balance -= 10
        response = requests.get('https://api.thecatapi.com/v1/images/search').json()[0].get('url')
        bot.send_photo(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, 'У вас недостаточно денег')


@bot.message_handler(func=lambda message: message.text == 'Перевертыши')
def invert(message):
    len_of_word = choice(range(10, 15))
    word = choices(['0', '1'], k=len_of_word)
    bot.send_message(message.chat.id, f'Нужно написать те же цифры, только наоборот (Вместо 1 0, вместо 0 1) \n'
                                      f'{"".join(word)}')

    def analysis_func(user_message):
        nonlocal word
        try:
            f = True
            for i in range(len(user_message.text)):
                if user_message.text[i] == '1':
                    k = '0'
                elif user_message.text[i] == '0':
                    k = '1'
                else:
                    raise IndexError
                if k != word[i]:
                    f = False
                    break
            if f and len(word) == len(user_message.text):
                session.query(User).filter(User.user_id == user_message.from_user.id).first().balance += 100
                session.commit()
                bot.send_message(message.chat.id, 'Вы написали все правильно, +100 денег', reply_markup=starting_menu())
            else:
                bot.send_message(message.chat.id, 'Вы ошиблись', reply_markup=starting_menu())
        except IndexError:
            bot.send_message(message.chat.id, 'Ваше сообщение некорректное', reply_markup=starting_menu())

    bot.register_next_step_handler(message, analysis_func)


@bot.message_handler(func=lambda message: message.text == "Магазин")
def shop(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    cats_button = button('Коты')
    menu_button = button('Назад в меню')
    markup.add(cats_button, menu_button)
    bot.send_message(message.chat.id, 'Получить 1 картинку котов стоит 10 монет', reply_markup=markup)


bot.polling(none_stop=True)

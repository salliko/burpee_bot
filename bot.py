# -*- encoding: utf-8 -*-

import datetime
import sqlite3

import telebot

import settings


try:
    bot = telebot.TeleBot(settings.TOKEN)

    conn = sqlite3.connect(settings.BD_PATH, check_same_thread=False)
    cursor = conn.cursor()


    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        bot.reply_to(message, 'Hello, what\'s up?')


    @bot.message_handler(func=lambda message: True)
    def write_result(message):
        if message.text.isdigit():
            curr_date = datetime.datetime.now().date().isoformat()
            cursor.execute('select user_id from users where user_telegram_id = %s' % (message.from_user.id))
            user_id = cursor.fetchone()[0]
            cursor.execute("""
                insert into burpee_results (user_id, sum, date) 
                values (%s, %s, %s)
            """ % (user_id, message.text, curr_date))
            bot.reply_to(message, 'Результат записан.')
            conn.commit()
        else:
            bot.reply_to(message, 'Результат должен быть числом.')


    bot.polling()
except Exception as e:
    pass
finally:
    cursor.close()
    conn.close()

# -*- encoding: utf-8 -*-

import datetime
import sqlite3

import telebot
from telebot import types

import settings

ADD_RESULT = 'Добавить результат'
MONTHLY_LEADERS = 'Лидеры за месяц'
MY_DATA = 'Мои данные'
DAY = 'День'
WEEK = 'Неделя'
MONTH = 'Месяц'
BACK = 'Назад'


try:
    bot = telebot.TeleBot(settings.TOKEN)

    conn = sqlite3.connect(settings.BD_PATH, check_same_thread=False)
    cursor = conn.cursor()

    def format_leaderboard_data(leaders):
        """Приводим данные полученные из бд к приятному восприятию. :)"""
        basket_of_medals = ['🥉', '🥈', '🥇']
        formatted_list = []
        header_leaderboard = 'Список лидеров за месяц.\n\n'

        for leader in leaders:
            medal = '🏋'
            if basket_of_medals:
                medal = basket_of_medals.pop()
            formatted_list.append(f"{medal} {leader[0]} ({leader[1]})")
        return header_leaderboard + '\n'.join(formatted_list)


    def get_month_leaderboard(message):
        """Получить лидеров берпи за текущий месяц."""
        date = datetime.datetime.now().date()
        cursor.execute("""
            select
              u.username,
              sum(br.amount) as amount
            from burpee_results br
            left join users u on br.user_id = u.user_id
            where strftime('%m', br.date_completion) = ?
            group by u.username
            order by amount desc
            limit 10
        """, (str(date.month),))

        bot.reply_to(message, format_leaderboard_data(cursor.fetchall()))

    def write_result(message):
        if message.text.isdigit():
            curr_date = datetime.datetime.now().date().isoformat()
            cursor.execute('select user_id from users where user_telegram_id = %s' % (message.from_user.id))
            user_id = cursor.fetchone()[0]
            cursor.execute("""
                insert into burpee_results (user_id, amount, date_completion)
                values (?, ?, ?)
            """, (user_id, message.text, curr_date))
            bot.reply_to(message, 'Результат записан.')
            conn.commit()
        else:
            bot.reply_to(message, 'Результат должен быть числом.')

    def get_my_data(message):
        markup = types.ReplyKeyboardMarkup()
        item1 = types.KeyboardButton(DAY)
        item2 = types.KeyboardButton(WEEK)
        item3 = types.KeyboardButton(MONTH)
        item4 = types.KeyboardButton(BACK)
        markup.add(item1, item2, item3, item4)
        msg = bot.send_message(message.chat.id, f'{MY_DATA}: ', reply_markup=markup)
        bot.register_next_step_handler(msg, process_step)


    def process_step(msg):
        if msg.text == MONTHLY_LEADERS:
            get_month_leaderboard(msg)
        elif msg.text == MY_DATA:
            get_my_data(msg)
        elif msg.text == DAY:
            pass
        elif msg.text == WEEK:
            pass
        elif msg.text == MONTH:
            pass
        elif msg.text == BACK:
            send_welcome(msg)
        elif msg.text == ADD_RESULT:
            write_result(msg)


    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        markup = types.ReplyKeyboardMarkup()

        itembtn1 = types.KeyboardButton(ADD_RESULT)
        itembtn2 = types.KeyboardButton(MONTHLY_LEADERS)
        itembtn3 = types.KeyboardButton(MY_DATA)
        markup.add(itembtn1, itembtn2, itembtn3)
        msg = bot.send_message(message.chat.id, 'Menu:', reply_markup=markup)
        bot.register_next_step_handler(msg, process_step)


    @bot.message_handler(commands=['help'])
    def send_welcome(message):
        pass

    bot.polling()
except Exception as e:
    pass
finally:
    cursor.close()
    conn.close()

# -*- encoding: utf-8 -*-

import datetime
import sqlite3

import telebot

import settings


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


    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        bot.reply_to(message, 'Hello, what\'s up?')

    @bot.message_handler(commands=['leaderboard'])
    def get_weekly_leaderboard(message):
        """Получить лидеров берпи за неделю."""
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


    @bot.message_handler(func=lambda message: True)
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


    bot.polling()
except Exception as e:
    pass
finally:
    cursor.close()
    conn.close()

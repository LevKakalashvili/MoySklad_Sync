"""Модуль описывает функции для работы сервиса."""
import datetime

import utils.file_utils
from moysklad.moysklad_class_lib import ms, GoodsType
from tbot.tbot import bot


def send_sales_file_to_telegram(chat_id: int) -> bool:
    # Получаем файл с продажами за сегодня
    file = ms.save_to_file_retail_demand_by_period(
        good_type=GoodsType.alco,
        start_period=datetime.datetime.today(),
        end_period=None
    )

    if file:
        if file != '':
            bot.send_message(chat_id, 'Касатики, вот файл с продажами за сегодня.')
            # Отправляем файл.
            bot.send_document(chat_id, open(file, 'rb'))
            # Удаляем отправленный файл с диска.
            utils.file_utils.remove_file(file)
            return True
        else:
            bot.send_message(chat_id, 'Не удалось подготовить файл')
    else:
        bot.send_message(chat_id, 'Не удалось подготовить файл')
    return False

# пример кода для телебота взят https://habr.com/ru/post/580408/
import datetime
import logging.config

import telebot

import logger_config
from moysklad.moysklad_class_lib import ms, GoodsType
from privatedata.tbot_privatedata import TOKEN
import utils.file_utils

# Инициализация
logging.config.dictConfig(logger_config.LOGGING_CONF)
# Логгер для Telegram бота
logger = logging.getLogger('tbot')
# создаем бота
bot = telebot.TeleBot(TOKEN, parse_mode=None)


@bot.message_handler(commands=['egais'])
def start_message(message: telebot.types.Message) -> None:
    logger.debug('Приняли команду: ' + message.json['text'])
    bot.send_message(message.chat.id, 'Готовлю данные...')

    # получаем ссылку на файл товаров ЕГАИС, проданных за прошедший день
    file = ms.save_to_file_retail_demand_by_period(
        good_type=GoodsType.alco,
        start_period=datetime.datetime.today() - datetime.timedelta(days=1),
        end_period=None
    )

    if file:
        if file != '':
            # отправляем файл
            bot.send_document(message.chat.id, open(file, 'rb'))
            logger.debug(f'Отправили файл в чат {file}')
            # удаляем отправленный файл с диска
            utils.file_utils.remove_file(file)
        else:
            bot.send_message(message.chat.id, 'Не удалось подготовить файл')
            logger.debug('Не удалось подготовить файл: нет имени файла')
    else:
        bot.send_message(message.chat.id, 'Не удалось подготовить файл')
        logger.error('Не удалось подготовить файл')


def run() -> None:
    bot.polling(none_stop=True)


if __name__ == '__main__':
    run()

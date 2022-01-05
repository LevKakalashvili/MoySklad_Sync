# пример кода для телебота взят https://habr.com/ru/post/580408/
import datetime
import logging.config
import os

import telebot

import logger_config
import moysklad.moysklad_class_lib as ms_class_lib
from privatedata.tbot_privatedata import TOKEN
import utils.file_utils

logging.config.dictConfig(logger_config.LOGGING_CONF)
logger = logging.getLogger('tbot')

# создаем бота
bot = telebot.TeleBot(TOKEN, parse_mode=None)


@bot.message_handler(commands=['egais'])
def start_message(message: telebot.types.Message) -> None:
    logger.debug('Приняли команду: ' + message.json['text'])
    bot.send_message(message.chat.id, 'Готовлю данные...')

    ms = ms_class_lib.MoySklad()

    if os.environ.get('DEBUG') == 'True':
        ms.get_token(request_new=True)
    else:
        ms.get_token(request_new=False)

    # получаем список товаров ЕГАИС, проданных за прошедший день
    date = datetime.datetime.today() - datetime.timedelta(days=3)
    ms.get_retail_demand_by_period(ms_class_lib.GoodsType.alco, date)

    if ms.sold_goods:
        # Сохраняем списания для ЕГАИС в файл ссылку xlsx, отправляем в чат
        send_file = utils.file_utils.save_to_excel(
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Списание_ЕГАИС'),  # путь до /MoySklad
            ms.sold_goods, date)

        if send_file != '':
            # отправляем файл
            bot.send_document(message.chat.id, open(send_file, 'rb'))
            logger.debug(f'Отправили файл в чат {send_file}')
            # удаляем отправленный файл с диска
            utils.file_utils.remove_file(send_file)
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

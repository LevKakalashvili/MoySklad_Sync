# пример кода взят https://habr.com/ru/post/580408/
import logger_config
import project_settings
import telebot
import datetime
import os, sys
import logging
import logging.config

sys.path.insert(1, project_settings.PROJECT_PATH)

import tbot.tbot_privatedata as tbot_privatedata
import moysklad.moysklad_class_lib as ms_class_lib
import googledrive.googledrive_class_lib as gs_class_lib
import googledrive.googlesheets_vars as gs_vars
import utils.file_utils


logging.config.dictConfig(logger_config.LOGGING_CONF)
logger = logging.getLogger("tbot")

bot = telebot.TeleBot(tbot_privatedata.TOKEN,  parse_mode = None)


@bot.message_handler(commands=['egais'])
def start_message(message):
    send_file = ''
    unsuccess = False
    try:
        logger.debug("Приняли команду: " + message.json['text'])
        bot.send_message(message.chat.id, "Готовлю данные...")

        ms = ms_class_lib.MoySklad()
        if not (ms is None):
            logger.debug("Создали объект ms")

        # получаем список товаров, проданых за прошедший день
        str_date_start = str(datetime.datetime.now().date() - datetime.timedelta(days=1)) + ' 00:00:00'
        str_date_end = str(datetime.datetime.now().date() - datetime.timedelta(days=1)) + ' 23:59:00'
        sold_goods = ms.get_retail_demand_by_period(str_date_start, str_date_end)

        if len(sold_goods) == 0:
            logger.error(f"Не получили список товаров из МС, проданых за период {str_date_start} - {str_date_end}:"
                         f" len(sold_goods) = {len(sold_goods)}")
            unsuccess = True
        else:
            logger.debug(f"Получили список товаров из МС, проданых за период {str_date_start} - {str_date_end}:"
                         f" len(sold_goods) = {len(sold_goods)}")

        if not unsuccess:
            # корректироуем список, удаляем из списка проданных товаров, то что не нужно списывать в ЕГАИС
            sold_goods = ms.get_goods_for_egais(sold_goods)

            if len(sold_goods) == 0:
                logger.error(f"Не получили скорректированный список товаров: len(sold_goods) = {len(sold_goods)}")
                unsuccess = True

            else:
                logger.debug(f"Получили скорректированный список товаров: len(sold_goods) = {len(sold_goods)}")

        if not unsuccess:
            gs = gs_class_lib.GoogleSheets()
            # получаем таблицу соответствий
            compl_table_egais = gs.get_data(gs_vars.SPREESHEET_ID_EGAIS,
                                            gs_vars.LIST_NAME_EGAIS,
                                            gs_vars.FIRST_CELL_EGAIS + ':' + gs_vars.LAST_COLUMN_EGAIS + '2000')

            if len(compl_table_egais) == 0:
                logger.error(f"Не получили таблицу соответствий из GoogleSheet: len(compl_table_egais) "
                             f"= {len(compl_table_egais)}")
                unsuccess = True
            else:

                logger.debug(
                    f"Получили таблицу соответствий из GoogleSheet: len(compl_table_egais) = {len(compl_table_egais)}")

        if not unsuccess:
            # соотносим проданные товары с наименованиями ЕГАИС
            compl_table_egais = ms.get_goods_compliance_egais(sold_goods, compl_table_egais)

            if len(compl_table_egais) == 0:
                logger.error(f"Не получили соотвествие названий ЕГАИС: len(compl_table_egais) = {len(compl_table_egais)}")
                unsuccess = True
            else:
                logger.debug(f"Получили соотвествие названий ЕГАИС: len(compl_table_egais) = {len(compl_table_egais)}")

        if not unsuccess:
            # сохраняем списания для ЕГАИС в файл. ссылку на excel, отправляем в чат
            send_file = utils.file_utils.save_to_excel(f'{os.path.abspath(os.curdir)}/Списание_ЕГАИС', compl_table_egais)


            if send_file != '':
                # отправляем файл
                bot.send_document(message.chat.id, open(send_file, "rb"))
                logger.debug(f"Отправили файл в чат {send_file}")
                # удаляем отправленный файл с диска
                utils.file_utils.remove_file(send_file)
            else:
                bot.send_message(message.chat.id, "Не удалось подготовить файл")
                logger.debug(f"Не удалось подготовить файл: нет имени файла")
                unsuccess = True

        if unsuccess:
            bot.send_message(message.chat.id, "Не удалось подготовить файл")

    except Exception as error:
        bot.send_message(message.chat.id, "Не удалось подготовить файл")
        logger.exception(f"Не удалось подготовить файл. " + error.args[0])

def run():
    bot.polling(none_stop=True)


if __name__ == '__main__':
    run()

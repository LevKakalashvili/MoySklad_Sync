# пример кода взят https://habr.com/ru/post/580408/
import logger_config
import telebot
import datetime
import os
import logging.config
import privatedata.tbot_privatedata as tbot_privatedata
import moysklad.moysklad_class_lib as ms_class_lib
import googledrive.googledrive_class_lib as gs_class_lib
import googledrive.googlesheets_vars as gs_vars
import utils.file_utils

# sys.path.insert(1, project_settings.PROJECT_PATH)

logging.config.dictConfig(logger_config.LOGGING_CONF)
logger = logging.getLogger("tbot")

bot = telebot.TeleBot(tbot_privatedata.TOKEN, parse_mode=None)


@bot.message_handler(commands=['egais'])
def start_message(message):
    send_file = ''
    success = False
    try:
        logger.debug("Приняли команду: " + message.json['text'])
        bot.send_message(message.chat.id, "Готовлю данные...")

        ms = ms_class_lib.MoySklad()
        ms.get_token()

        # получаем список товаров, проданых за прошедший день
        sold_goods = ms.get_retail_demand_by_period(datetime.datetime.today(),
                                                    datetime.datetime.today() - datetime.timedelta(days=1))

        if not sold_goods:
            logger.error(f"Не получили список товаров из МС, проданых за период "
                         f"{datetime.datetime.today().strptime('%Y-%m-%d 00:00:00')} - "
                         f"{datetime.datetime(datetime.datetime.today() - datetime.timedelta(days=1)).strptime('%Y-%m-%d 23:59:00')}:"
                         f" len(sold_goods) = {len(sold_goods)}")
        else:
            logger.debug(f"Получили список товаров из МС, проданых за период {str_date_start} - {str_date_end}:"
                         f" len(sold_goods) = {len(sold_goods)}")

        if not sold_goods:
            # корректироуем список, удаляем из списка проданных товаров, то что не нужно списывать в ЕГАИС
            sold_goods = ms.get_goods_for_egais(sold_goods)

            if not sold_goods:
                logger.error(f"Не получили скорректированный список товаров: len(sold_goods) = {len(sold_goods)}")

            else:
                logger.debug(f"Получили скорректированный список товаров: len(sold_goods) = {len(sold_goods)}")

        if sold_goods:
            gs = gs_class_lib.GoogleSheets()
            # получаем таблицу соответствий
            compl_table_egais = gs.get_data(gs_vars.SPREEDSHEET_ID_EGAIS,
                                            gs_vars.LIST_NAME_EGAIS,
                                            gs_vars.FIRST_CELL_EGAIS + ':' + gs_vars.LAST_COLUMN_EGAIS + '2000')

            if not compl_table_egais:
                logger.error(f"Не получили таблицу соответствий из GoogleSheet: len(compl_table_egais) "
                             f"= {len(compl_table_egais)}")
            else:

                logger.debug(
                    f"Получили таблицу соответствий из GoogleSheet: len(compl_table_egais) = {len(compl_table_egais)}")

        if compl_table_egais:
            # соотносим проданные товары с наименованиями ЕГАИС
            compl_table_egais = ms.get_goods_compliance_egais(sold_goods, compl_table_egais)

            if not compl_table_egais:
                logger.error(
                    f"Не получили соотвествие названий ЕГАИС: len(compl_table_egais) = {len(compl_table_egais)}")
                success = False
            else:
                logger.debug(f"Получили соотвествие названий ЕГАИС: len(compl_table_egais) = {len(compl_table_egais)}")

        if succescompl_table_egais:
            # сохраняем списания для ЕГАИС в файл. ссылку на excel, отправляем в чат
            send_file = utils.file_utils.save_to_excel(
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Списание_ЕГАИС'),  # путь до /MoySklad
                compl_table_egais)

            if send_file != '':
                # отправляем файл
                bot.send_document(message.chat.id, open(send_file, "rb"))
                logger.debug(f"Отправили файл в чат {send_file}")
                # удаляем отправленный файл с диска
                utils.file_utils.remove_file(send_file)
            else:
                bot.send_message(message.chat.id, "Не удалось подготовить файл")
                logger.debug(f"Не удалось подготовить файл: нет имени файла")
        else:
            bot.send_message(message.chat.id, "Не удалось подготовить файл")

    except Exception as error:
        bot.send_message(message.chat.id, "Не удалось подготовить файл")
        logger.exception(f"Не удалось подготовить файл. " + error.args[0])


def run():
    bot.polling(none_stop=True)


if __name__ == '__main__':
    print(ms_class_lib.test())
    # run()

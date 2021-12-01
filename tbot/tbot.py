# пример кода взят https://habr.com/ru/post/580408/
import telebot

import datetime
import tbot.tbot_privatedata as tbp
import moysklad.moysklad_class_lib as ms_class_lib
import googledrive.googledrive_class_lib as gs_class_lib
import googledrive.googlesheets_vars as gs_vars
import utils.file_utils


bot = telebot.TeleBot(tbp.TOKEN,  parse_mode = None)


@bot.message_handler(commands=['egais'])
def start_message(message):
    try:
        bot.send_message(message.chat.id, "Готовлю данные...")
        ms = ms_class_lib.MoySklad()
        # получаем список товаров, проаданых за прошедший день
        sold_goods = ms.get_retail_demand_by_period(
            str(datetime.datetime.now().date() - datetime.timedelta(days=1)) + ' 00:00:00',
            str(datetime.datetime.now().date() - datetime.timedelta(days=1)) + ' 23:59:00')
        # корректироуем список, удаляем из списка проданных товаров, то что не нужно списывать в ЕГАИС
        sold_goods = ms.get_goods_for_egais(sold_goods)

        gs = gs_class_lib.GoogleSheets()
        # получаем таблицу соответсвий
        compl_table_egais = gs.get_data(gs_vars.SPREESHEET_ID_EGAIS,
                                        gs_vars.LIST_NAME_EGAIS,
                                        gs_vars.FIRST_CELL_EGAIS + ':' + gs_vars.LAST_COLUMN_EGAIS + '2000')

        # соотносим проданные товары с наименованиями ЕГАИС
        compl_table_egais = ms.get_goods_compliance_egais(sold_goods, compl_table_egais)

        # сохраняем списания для ЕГАИС в файл. ссылку на excel, отправляем в чат
        send_file = utils.file_utils.save_to_excel(f'../Списание_ЕГАИС', compl_table_egais)
        if send_file != '':
            # отправляем файл
            bot.send_document(message.chat.id, open(send_file, "rb"))
            # удаляем отправленный файл с диска
            utils.file_utils.remove_file(send_file)
        else:
            bot.send_message(message.chat.id, "Не удалось подготовить файл")

    except Exception as error:
        bot.send_message(message.chat.id, "Не удалось подготовить файл")

def run():
    bot.polling(none_stop=True)


if __name__ == '__main__':
    bot.polling(none_stop=True)

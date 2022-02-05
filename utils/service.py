"""Модуль описывает функции для работы сервиса."""
import datetime
from typing import List

import googledrive.googlesheets_vars as gs_vars
from googledrive.googledrive_class_lib import googlesheets
import utils.file_utils
from konturmarket.konturmarket_class_lib import GoodEGAIS
from konturmarket.konturmarket_class_lib import kmarket
from moysklad.moysklad_class_lib import ms, GoodsType
from tbot.tbot import bot


def send_sales_file_to_telegram(chat_id: int) -> bool:
    """Функция отправки заполненного файла с продажами в телеграм чат.

    :param chat_id: id телеграм чата, в который отправляется файл.
    """
    # Получаем файл с продажами за сегодня
    file_name: str = ms.save_to_file_retail_demand_by_period(
        good_type=GoodsType.alco,
        start_period=datetime.datetime.today(),
        end_period=None,
    )

    if file_name != '':
        bot.send_message(chat_id, 'Касатики, вот файл с продажами за сегодня.')
        # Отправляем файл.
        bot.send_document(chat_id, open(file_name, 'rb'))
        # Удаляем отправленный файл с диска.
        utils.file_utils.remove_file(file_name)
        return True
    else:
        bot.send_message(chat_id, 'Не удалось подготовить файл')
    return False


def update_goooglesheets_egais_assortment(chat_id: int) -> bool:
    """Функция обновления листа ЕГАИС наименований."""
    # Проверяем получилось залогиниться в сервисе
    if not kmarket.connection_OK:
        return False
    # Получаем список ЕГАИС наименований
    egais_goods: List[GoodEGAIS] = kmarket.get_egais_assortment()
    if egais_goods:
        # Сохранять в GoogleSheet будем только фасованный товар, тот что имеет значение аттрибута capacity
        data = [
            (
                egais_good.brewery.name,
                egais_good.name,
                f"'{egais_good.alco_code}",
                egais_good.get_description(),
            )
            for egais_good in egais_goods
            if egais_good.capacity is not None
        ]

        # Записываем данные в GoogleSheets
        result = googlesheets.send_data(data=data,
                                        spreadsheets_id=gs_vars.SPREEDSHEET_ID_EGAIS,
                                        list_name=gs_vars.LIST_NAME_EGAIS_ASSORTMNET,
                                        list_range=f'{gs_vars.FIRST_CELL_EGAIS_ASSORTMNET}:'
                                                   f'{gs_vars.LAST_COLUMN_EGAIS_ASSORTMNET}'
                                                   f'{len(egais_goods) + 1}',
                                        )
        if result:
            bot.send_message(chat_id, 'Касатики, обновил ЕГАИС справочник')
            return True
        else:
            bot.send_message(chat_id, 'Касатики, не смог обновить ЕГАИС справочник. Простите ;(')
            return False

"""В модуле хранятся описание классов."""
import datetime
import os
from collections import OrderedDict
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import requests
import logging
import logger_config


import googledrive.googledrive_class_lib as gs_class_lib
import googledrive.googlesheets_vars as gs_vars
import moysklad.moysklad_urls as ms_urls
import privatedata.moysklad_privatedata as ms_pvdata
from utils.file_utils import save_to_excel

logging.config.dictConfig(logger_config.LOGGING_CONF)
# Логгер для МойСклад
logger = logging.getLogger('moysklad')


class GoodsType(Enum):
    """Перечисление для определения, какой тип товаров необходимо получить.

    alco - алкогольная продукция (исключая разливное пиво).
    non_alco - не алкогольная продукция
    snack - закуски
    """

    alco = 1
    non_alco = 2
    snack = 3


@dataclass
class Good:
    """Класс описывает структуру товара."""
    commercial_name: str
    quantity: int
    price: Decimal
    egais_name: str = ''
    convert_name: bool = True

    def __post_init__(self) -> None:
        if self.convert_name:
            self.commercial_name = self._convert_name(self.commercial_name)

    @staticmethod
    def _convert_name(name: str) -> str:
        """Метод преобразует строку наименования вида.
        4Пивовара - Black Jesus White Pepper (Porter - American. OG 17, ABV 6.7%, IBU 69)
        к строке вида
        4Пивовара - Black Jesus White Pepper.

        :param name: Наименование товара.
        :type name: str
        :rtype: str
        """
        return name.split(' (')[0].replace('  ', ' ').strip()

    @property
    def to_tuple(self) -> Tuple[str, str, int, Decimal]:
        return self.commercial_name, self.egais_name, self.quantity, self.price


@dataclass()
class MoySklad:
    """Класс описывает работу с сервисом МойСклад по JSON
    API 1.2 https://dev.moysklad.ru/doc/api/remap/1.2/#mojsklad-json-api."""

    # токен для работы с сервисом
    # https://dev.moysklad.ru/doc/api/remap/1.2/#mojsklad-json-api-obschie-swedeniq-autentifikaciq
    _token: str = ''

    def set_token(self, request_new: bool = True) -> bool:
        """Получение токена для доступа и работы с МС по JSON API 1.2. При успешном ответе возвращаем True,
        в случае ошибок False.
        https://dev.moysklad.ru/doc/api/remap/1.2/#mojsklad-json-api-obschie-swedeniq-autentifikaciq.

        :param request_new: True, каждый раз будет запрашиваться новый токен,
            если False будет браться из moysklad_privatedata.py
        """
        logger.debug(f'Получаем токен для работы с сервисом МойСклад. request_new = {request_new}')
        # если необходимо запросить новый токен у сервиса
        if request_new:
            logger.debug('Пытаемся получить токен у MoySklad')
            # Получаем url запроса
            url: ms_urls.Url = ms_urls.get_url(ms_urls.UrlType.token)
            # Получаем заголовок запроса
            header: Dict[str, Any] = ms_urls.get_headers(self._token)

            # отправляем запрос в МС для получения токена
            try:
                response = requests.post(url.url, headers=header)
                response.raise_for_status()
            except requests.RequestException as error:
                logger.exception(f'Не удалось получить токен MoySklad: {error.args[0]}')
                return False

            self._token = response.json()['access_token']  # возвращаем токен
        else:
            self._token = ms_pvdata.TOKEN

        return True

    def get_retail_demand_by_period(
        self,
        good_type: GoodsType,
        start_period: datetime.datetime,
        end_period: Optional[datetime.datetime] = None,
    ) -> List[Good]:
        """Метод возвращает список, проданных товаров.
        Тип товаров определяется параметром good_type.

        :param good_type: Тип запрашиваемых товаров из сервиса.
        :type good_type: Перечисление типа товаров.
        :param start_period: начало запрашиваемого периода start_period 00:00:00.
        :param end_period: конец запрашиваемого периода end_period 23:59:00.
        """
        # Если токен не получен, возвращаем пустой список
        if not self._token:
            return []

        if end_period is None:
            end_period = start_period

        # Получаем список товаров из МС, проданных за период
        sold_goods: list[Good] = self._get_retail_demand_by_period(good_type, start_period, end_period)
        if not sold_goods:
            return []
        gs = gs_class_lib.GoogleSheets()

        if gs.service is None:
            return []

        # получаем таблицу соответствий
        compl_table_egais = gs.get_data(
            gs_vars.SPREEDSHEET_ID_EGAIS,
            gs_vars.LIST_NAME_EGAIS,
            f'{gs_vars.FIRST_CELL_EGAIS}:{gs_vars.LAST_COLUMN_EGAIS}2000',
        )
        # заполняем поле наименование ЕГАИС, проданных товаров
        self._fill_egais_name(compl_table_egais, sold_goods[:])

        return sold_goods

    def _get_retail_demand_by_period(
        self,
        good_type: GoodsType,
        start_period: datetime.datetime,
        end_period: datetime.datetime,
    ) -> List[Good]:
        """Метод заполняет поле sold_goods вызываемого инстанса класса, проданными товарами. Тип товаров определятся
        параметром good_type.

        :param good_type: Тип запрашиваемых товаров из сервиса.
        :type good_type: Перечисление типа товаров.
        :param start_period: начало запрашиваемого периода start_period 00:00:00.
        :param end_period: конец запрашиваемого периода end_period 23:59:00. Если не указа, то считается,
        как start_period 23:59:00.
        :return:
            В случе успешного завершения возвращается список, элементов. Элемент - экземпляр класса Good
                Наименование товара (str)
                Количество проданного товара за заданный промежуток времени (float)
                Стоимость единицы товара (float)
            В случае ошибки возвращается пустой список.
        :rtype: list[Good]
        """
        if not self._token:
            return []

        # Получаем url для отправки запроса в сервис
        url: ms_urls.Url = ms_urls.get_url(ms_urls.UrlType.retail_demand, start_period, end_period)
        # Получаем заголовки для запроса в сервис
        header: Dict[str, Any] = ms_urls.get_headers(self._token)
        try:
            response = requests.get(url.url, url.request_filter, headers=header)
            response.raise_for_status()
        except requests.RequestException as error:
            logger.exception(f'Не удалось получить продажи из сервиса MoySklad: {error.args[0]}')
            return []  # возвращаем пустой список

        # Проверяем получили ли в ответе не пустой список продаж response.json()['meta']['size'] - размер массива
        # в ответе len(response.json()['rows']) - размер массива в ответе, если это число меньше,
        # чем response.json()[ 'meta']['size'] то надо будет делать дополнительные запросы со смещением 100
        # словарь для хранения списка проданных товаров. Ключ - наименование, значение - список [количество
        # товара, цена]

        # Смотрим, вернулись ли нам данные в ответе
        if response.json()['meta']['size'] > 0:
            return self._get_goods_from_retail_demand(good_type, response.json()['rows'])

        return []

    @staticmethod
    def _need_save_position(good_type: GoodsType, sale_position: Dict[str, Any]) -> bool:
        # attributes - список аттрибутов sale_position['assortment']['attributes']
        if good_type == GoodsType.alco:
            # Если в сервисе не указан ни оди из аттрибутов "Розлив" - не указан, "Алкогольная продукция" - не отмечено,
            # то у товара не будет элемента словаря ['attributes'].
            # А sale_position['assortment']['attributes'] вызовет исключение KeyError
            attributes = sale_position['assortment'].get('attributes')
            if not attributes:
                return False

            # Если в сервисе у товара определен аттрибут "Розлив", то индекс аттрибута "Алкогольная продукция",
            # в массиве аттрибутов будет 1, если не определен, то индекс будет 0. это происходит т.к. аттрибут
            # "Алкогольная продукция", является обязательным для всех товаров
            #
            # Признак алкогольной продукции
            # дополнительное поле "Алкогольная продукция" в массиве ['attributes'] - элемент с индексом 1
            # True - чек-бокс установлен, False - не установлен
            # проверяем, что аттрибут "Алкогольная продукция" == True
            value = attributes[0]['value']
            if len(attributes) == 1 and value:
                return True
            # Признак разливного пива
            # дополнительное поле "Розлив" в массиве ['attributes'] - элемент с индексом 0
            # Возможные значения: Да, да, Нет, нет, пустая строка, аттрибут может отсутствовать
            elif len(attributes) == 2 and str(value).lower() != 'да':
                return True
        return False

    def _get_goods_from_retail_demand(self, good_type: GoodsType, ms_retail_demands: List[Any]) -> List[Good]:
        """Метод заполняет поле sold_goods вызываемого инстанса класса, проданными товарами.
        Тип товаров определяться параметром good_type. Список формируется из списка розничных продаж.

        :params good_type: Тип возвращаемых товаров.
        :params ms_retail_demands: Список розничных продаж, возвращаемый в ответе сервиса (response.json()['rows']),
         при запросе https://online.moysklad.ru/api/remap/1.2/entity/retaildemand
        """
        goods: Dict[str, Good] = OrderedDict()
        for retail_demand in ms_retail_demands:
            for sale_position in retail_demand['positions']['rows']:
                if good_type == GoodsType.alco:
                    # Если в сервисе у товара определен аттрибут "Розлив", то индекс аттрибута "Алкогольная продукция",
                    # в массиве аттрибутов будет 1, если не определен, то индекс будет 0. Т.к. аттрибут
                    # "Алкогольная продукция", является обязательным для всех товаров
                    # если товар удовлетворяет типу GoodsType.alco
                    if not self._need_save_position(good_type, sale_position):
                        # если товар не нужен переходим к следующему
                        continue

                    good = Good(
                        commercial_name=sale_position['assortment']['name'],
                        quantity=int(sale_position['quantity']),  # sale_position['quantity'] - float
                        price=Decimal(sale_position['price'] / 100)  # sale_position['price'] - float
                    )

                    # если товар уже есть в списке проданных
                    if good.commercial_name in goods:
                        # увеличиваем счетчик проданного товара
                        goods[good.commercial_name].quantity += good.quantity
                    else:
                        # добавляем товар в словарь проданных товаров
                        goods[good.commercial_name] = good
        # сортируем словарь и преобразуем в список
        return [good for name, good in sorted(goods.items())]

    @staticmethod
    def _fill_egais_name(comp_table: list[list[str]], sold_goods: list[Good]) -> None:
        """Метод заполняет поле ЕГАИС наименование у товара, на основе таблицы соответствий.

        :param comp_table: Таблица соответствий коммерческое наименование - наименование ЕГАИС.
        :type comp_table: Список списков. Элемент вложенного списка: [0] - коммерческое наименование, [1] - ЕГАИС
        наименование.
        """
        # comp_table - отсортированный список списков
        # [[Наименование, Наименование ЕГАИС], [Наименование, Наименование ЕГАИС], ...]
        if not comp_table:
            return

        # Т.к. мы не можем гарантировать, что вложенные списки в comp_table - списки из 2ух элементов,
        # то необходимо проверять их длину
        # Коммерческое наименование приводить нужно к нижнему регистру, т.к. в сервисе товар может храниться как
        # Aircraft - Рождественский Эль, а в таблице ЕГАИС как Aircraft - Рождественский эль
        temp_comp_table = {
            str(good[0]).lower(): good[1]
            for good in comp_table if len(good) > 1
        }
        for good in sold_goods:
            # находим товар в таблице соответствий
            eagis_name = temp_comp_table.get(good.commercial_name.lower())
            if eagis_name:
                # обновляем ЕГАИС наименование
                good.egais_name = eagis_name

    def save_to_file_retail_demand_by_period(self,
                                             good_type: GoodsType,
                                             start_period: datetime.datetime,
                                             end_period: Optional[datetime.datetime] = None
                                             ) -> str:
        """Метод сохраняет в файл .*xlsx список проданных товаров за определенный период.

        :param good_type: Тип сохраняемых товаров.
        :param start_period: Начало запрашиваемого периода start_period 00:00:00.
        :param end_period: Конец запрашиваемого периода end_period 23:59:00. Если не указана, то считается, как start_period 23:59:00.

        :return: Путь к файлу со списком проданных товаров.
        В случае успешного сохранения возвращается ссылка на файл.
        В случае ошибки возвращается пустая строка.
        """

        # Если токен не получен, возвращаем пустую строку
        if not self._token:
            return ''

        # Запрашиваем список проданных товаров, с заполненными наименованиями ЕГАИС
        sold_goods: List[Good] = self.get_retail_demand_by_period(
            good_type=good_type,
            start_period=start_period,
            end_period=end_period)

        if not sold_goods:
            return ''

        # Сохраняем списания для ЕГАИС в файл. Ссылку xlsx, возвращаем
        send_file = save_to_excel(
            os.path.join(os.path.dirname(
                os.path.dirname(__file__)),
                'Списание_ЕГАИС'),  # путь до /MoySklad
            sold_goods[:],
            start_period - end_period if end_period is not None else start_period)
        return send_file


# Инициализация
# Выполняется один раз при импорте модуля
ms = MoySklad()
ms.set_token(request_new=True)

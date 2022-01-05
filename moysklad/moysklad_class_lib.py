"""В модуле хранятся описание классов."""
import datetime
import logging
import logging.config
from enum import Enum
from typing import Any, Dict, List

import requests

import googledrive.googledrive_class_lib as gs_class_lib
import googledrive.googlesheets_vars as gs_vars
import logger_config
import moysklad.moysklad_urls as ms_urls
import privatedata.moysklad_privatedata as ms_pvdata


class GoodsType(Enum):
    """Перечисление для определения, какой тип товаров необходимо получить.

    alco - алкогольная продукция (исключая разливное пиво).
    non_alco - не алкогольная продукция
    snack - закуски
    """

    alco = 1
    non_alco = 2
    snack = 3


class Good:
    """Класс описывает структуру товара."""

    def __init__(self, commercial_name: str, egais_name: str, quantity: float, price: float, convert_name: bool = True):
        """Конструктор класса (flake8)."""
        self.commercial_name: str = commercial_name  # коммерческое наименование
        if convert_name:
            self.commercial_name = self._convert_name(commercial_name)  # коммерческое наименование
        self.egais_name: str = egais_name  # наименование ЕГАИС
        self.quantity: float = quantity  # проданное количество
        self.price: float = price  # цена

    def _convert_name(self, name: str) -> str:
        """Метод преобразует строку наименования вида.
        4Пивовара - Black Jesus White Pepper (Porter - American. OG 17, ABV 6.7%, IBU 69)
        к строке вида
        4Пивовара - Black Jesus White Pepper.

        :param name: наименование товара
        :type name: str
        :rtype: str
        """
        return name.split(' (')[0].replace('  ', ' ').strip()

    def __iter__(self):  # type: ignore
        """Итератор."""
        for each in self.__dict__.values():
            yield each


class MoySklad:
    """Класс описывает работу с сервисом МойСклад по JSON API 1.2 https://dev.moysklad.ru/doc/api/remap/1.2/#mojsklad-json-api."""

    def __init__(self) -> None:
        """Конструктор класса (flake8)."""
        logging.config.dictConfig(logger_config.LOGGING_CONF)
        self.logger = logging.getLogger('moysklad')
        # токен для работы с сервисом
        # https://dev.moysklad.ru/doc/api/remap/1.2/#mojsklad-json-api-obschie-swedeniq-autentifikaciq
        self._token: str = ''

        self.sold_goods: list[Good] = []  # Отсортированный по Good.commercial_name, cписок проданных товаров

    def get_token(self, request_new: bool = True) -> bool:
        """Получение токена для доступа и работы с МС по JSON API 1.2. При успешном ответе возвращаем True, в случае ошибок False. https://dev.moysklad.ru/doc/api/remap/1.2/#mojsklad-json-api-obschie-swedeniq-autentifikaciq.

        :param request_new: True, каждый раз будет запрашиваться новый токен, если False будет браться из moysklad_privatedata.py
        """
        self.logger.debug(f'Получаем токен для работы с сервисом МойСклад. request_new = {request_new}')
        # если необходимо запросить новый токен у сервиса
        if request_new:
            # определяем заголовок
            self.logger.debug('Пытаемся получить токен у MoySklad')

            url: ms_urls.Url = ms_urls.get_url(ms_urls.UrlType.token)
            header: Dict[str, Any] = ms_urls.get_headers(self._token)

            # отправляем запрос в МС для получения токена
            try:
                response = requests.post(url.url, headers=header)
                response.raise_for_status()
            except requests.RequestException as error:
                self.logger.exception(f'Не удалось получить токен MoySklad: {error.args[0]}')
                return False

            self._token = response.json()['access_token']  # возвращаем токен
        else:
            self._token = ms_pvdata.TOKEN

        return True

    def get_retail_demand_by_period(self, _type: GoodsType, start_period: datetime.datetime,
                                    end_period: datetime.datetime = None) -> None:
        """Метод заполняет поле sold_goods вызываемого инстанса класса, проданными товарами. Тип товаров определяться параметром _type.

        :param _type: Тип запрашиваемых товаров из сервиса.
        :type _type: Перечисление типа товаров.
        :param start_period: начало запрашиваемого периода start_period 00:00:00
        :param end_period: конец запрашиваемого периода end_period 23:59:00. Если не указана, то считается,
        как start_period 23:59:00.
        """
        if end_period is None:
            end_period = start_period

        # Получаем список товаров из МС, проданных за период
        self._get_retail_demand_by_period(_type, start_period, end_period)

        if self.sold_goods:
            gs = gs_class_lib.GoogleSheets()

            if gs.service is not None:
                # получаем таблицу соответствий
                compl_table_egais = gs.get_data(gs_vars.SPREEDSHEET_ID_EGAIS,
                                                gs_vars.LIST_NAME_EGAIS,
                                                f'{gs_vars.FIRST_CELL_EGAIS}:{gs_vars.LAST_COLUMN_EGAIS}2000')
                if compl_table_egais:
                    # заполняем поле наименование ЕГАИС, проданных товаров
                    self._fill_egais_name(compl_table_egais)

    def _get_retail_demand_by_period(self, _type: GoodsType, start_period: datetime.datetime,
                                     end_period: datetime.datetime = None) -> None:
        """Метод заполняет поле sold_goods вызываемого инстанса класса, проданными товарами. Тип товаров определяться параметром _type.

        :param _type: Тип запрашиваемых товаров из сервиса.
        :type _type: Перечисление типа товаров.
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
        if self._token:
            url: ms_urls.Url = ms_urls.get_url(ms_urls.UrlType.retail_demand, start_period, end_period)
            header: Dict[str, Any] = ms_urls.get_headers(self._token)
            try:
                response = requests.get(url.url, url.request_filter, headers=header)
                response.raise_for_status()
            except requests.RequestException as error:
                self.logger.exception(f'Не удалось получить продажи из сервиса MoySklad: {error.args[0]}')
                return None  # возвращаем пустой список

            # Проверяем получили ли в ответе не пустой список продаж response.json()['meta']['size'] - размер массива
            # в ответе len(response.json()['rows']) - размер массива в ответе, если это число меньше,
            # чем response.json()[ 'meta']['size'] то надо будет делать дополнительные запросы со смещением 100
            # словарь для хранения списка проданных товаров. Ключ - наименование, значение - список [количество
            # товара, цена]

            # Смотрим, вернулись ли нам данные в ответе
            if response.json()['meta']['size'] > 0:
                self._get_goods_from_retail_demand(_type, response.json()['rows'])
        return None

    def _need_save_position(self, _type: GoodsType, sale_position: List[Any]) -> bool:

        # attributes - список аттрибутов sale_position['assortment']['attributes']
        if _type == GoodsType.alco:
            # Если в сервисе не указан ни оди из аттрибутов "Розлив" - не указан, "Алкогольная продукция" - не отмечено,
            # то у товара не будет элемента словаря ['attributes'].
            # А sale_position['assortment']['attributes'] вызовет исключение KeyError
            if 'attributes' in sale_position['assortment']:
                # Если в сервисе у товара определен аттрибут "Розлив", то индекс аттрибута "Алкогольная продукция",
                # в массиве аттрибутов будет 1, если не определен, то индекс будет 0. Т.к. аттрибут
                # "Алкогольная продукция", является обязательным для всех товаров
                # Признак алкогольной продукции
                # дополнительное поле "Алкогольная продукция" в массиве ['attributes'] - элемент с индексом 1
                # True - чек-бокс установлен, False - не установлен
                # проверяем, что аттрибут "Алкогольная продукция" == True
                if len(sale_position['assortment']['attributes']) == 1 and sale_position['assortment']['attributes'][0]['value']:
                    return True
                # Признак разливного пива
                # дополнительное поле "Розлив" в массиве ['attributes'] - элемент с индексом 0
                # Возможные значения: Да, да, Нет, нет, пустая строка, аттрибут может отсутствовать
                elif len(sale_position['assortment']['attributes']) == 2 and str(sale_position['assortment']['attributes'][0]['value']).lower() != 'да':
                    return True
        return False

    def _get_goods_from_retail_demand(self, _type: GoodsType, ms_retail_demands: List[Any]) -> None:
        """Метод заполняет поле sold_goods вызываемого инстанса класса, проданными товарами. Тип товаров определяться параметром _type. Список формируется из списка розничных продаж.

        :params _type: Тип возвращаемых товаров.
        :params ms_retail_demands: Список розничных продаж, возвращаемый в ответе сервиса (response.json()['rows']),
         при запросе https://online.moysklad.ru/api/remap/1.2/entity/retaildemand
        """
        goods: Dict[str, Good] = {}
        for retail_demand in ms_retail_demands:
            for sale_position in retail_demand['positions']['rows']:
                if _type == GoodsType.alco:
                    # Если в сервисе у товара определен аттрибут "Розлив", то индекс аттрибута "Алкогольная продукция",
                    # в массиве аттрибутов будет 1, если не определен, то индекс будет 0. Т.к. аттрибут
                    # "Алкогольная продукция", является обязательным для всех товаров
                    # если товар удовлетворяет типу GoodsType.alco
                    if self._need_save_position(_type, sale_position):
                        good = Good(sale_position['assortment']['name'], '', sale_position['quantity'], sale_position['price'] / 100)
                    # если товар не нужен переходим к следующему
                    else:
                        continue

                    # если товар уже есть в списке проданных
                    if good.commercial_name in goods:
                        # увеличиваем счетчик проданного товара
                        goods[good.commercial_name].quantity += good.quantity
                    # добавляем товар в словарь проданных товаров
                    else:
                        # добавляем товар в словарь проданных товаров
                        goods[good.commercial_name] = good
        # сортируем словарь и преобразуем в список
        self.sold_goods = [good for key, good in sorted(goods.items())]

    def _fill_egais_name(self, comp_table: list[list[str]]) -> None:
        """Метод заполняет поле ЕГАИС наименование у товара, на основе таблицы соответствий.

        :param comp_table: Таблица соответствий коммерческое наименование - наименование ЕГАИС.
        :type comp_table: Список списков. Элемент вложенного списка: [0] - коммерческое наименование, [1] - ЕГАИС
        наименование.
        """
        # comp_table - отсортированный список списков
        # [[Наименование, Наименование ЕГАИС], [Наименование, Наименование ЕГАИС], ...]
        if not comp_table:
            return None

        # Т.к. мы не можем гарантировать, что вложенные списки в comp_table - списки из 2ух элементов,
        # то необходимо проверять их длину
        # Коммерческое наименование приводить нужно к нижнему регистру, т.к. в сервисе товар может храниться как
        # Aircraft - Рождественский Эль, а в таблице ЕГАИС как Aircraft - Рождественский эль
        temp_comp_table = {str(good[0]).lower(): good[1] for good in comp_table if len(good) > 1}
        for good in self.sold_goods:
            # находим товар в таблице соответствий
            if str(good.commercial_name).lower() in temp_comp_table:
                # обновляем ЕГАИС наименование
                good.egais_name = temp_comp_table[str(good.commercial_name).lower()]

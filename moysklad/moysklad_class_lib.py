""" В модуле хранятся описание классов.

"""
from typing import NamedTuple
import os

import requests
import logging
import base64
import datetime
from urllib.parse import urljoin
import logging.config
import logger_config
import privatedata.moysklad_privatedata as ms_pvdata
import moysklad.moysklad_urls as ms_urls
import googledrive.googledrive_class_lib as gs_class_lib
import googledrive.googlesheets_vars as gs_vars


class Good(NamedTuple):
    """ Класс описывает структуру товара """
    commercial_name: str = ''  # коммерческое наименование
    egais_name: str = ''  # наименование ЕГАИС
    quantity: float = 0  # проданное количество
    price: float = 0  # цена


class MoySklad:
    """ Класс описывает работу с сервисом МойСклад по JSON API 1.2
    https://dev.moysklad.ru/doc/api/remap/1.2/#mojsklad-json-api
    """

    def __init__(self) -> None:
        logging.config.dictConfig(logger_config.LOGGING_CONF)
        self.logger = logging.getLogger("moysklad")
        # токен для работы с сервисом
        # https://dev.moysklad.ru/doc/api/remap/1.2/#mojsklad-json-api-obschie-swedeniq-autentifikaciq
        self._token = ''

        self.sold_goods = []  # список проданных товаров за период
        self.sold_goods_egais = []  # список проданных товаров для списания в ЕГАИС

    def get_token(self, request_new=False) -> bool:
        """ Получение токена для доступа и работы с МС по JSON API 1.2. При успешном ответе возвращаем True,
        в случае ошибок False
        # https://dev.moysklad.ru/doc/api/remap/1.2/#mojsklad-json-api-obschie-swedeniq-autentifikaciq
        request_new = True, каждый раз будет запрашиваться новый, если False будет браться из moysklad_privatedata.py
        """
        self.logger.debug(f"Получаем токен для работы с сервисом МойСклад. request_new = {request_new}")
        # если необходимо запросить новый токен у сервиса
        if request_new:
            # определяем заголовок
            self.logger.debug(f"Пытаемся получить токен у MoySklad")
            headers = {
                'Authorization': 'Basic' + str(base64.b64encode((ms_pvdata.USER + ':' + ms_pvdata.PASSWORD).encode()))
            }
            # отправляем запрос в МС для получения токена
            try:
                response = requests.post(urljoin(ms_urls.JSON_URL, 'security/token'), headers=headers)
                response.raise_for_status()
            except requests.RequestException as error:
                self.logger.exception(f"Не удалось получить токен MoySklad: {error.args[0]}")
                return False

            if response.json()['access_token'] != '':
                self._token = response.json()['access_token']  # возвращаем токен
                self.logger.debug(f"Получили токен у MoySklad")
                return True
            else:
                self.logger.error(f"Не удалось получить токен MoySklad")
                return False
        else:
            self.logger.debug(f"Получаем токен для работы с сервисом МойСклад из файла. request_new = {request_new}")
            self._token = ms_pvdata.TOKEN
            return True

    def _get_goods_compliance_egais(self, sold_goods: list, comp_table: list) -> list:
        """
        Метод сравнивает два списка sold_goods и comp_table, возвращает новый sold_goods, c заполненными наименованиями
        ЕГАИС
        :param sold_goods: список товаров, каждый элемент - инстанс класса Good
        :param comp_table:
        :return: список товаров, c заполненным Good.egais_name, каждый элемент инстанс класса Good
        """

        # sold_goods - отсортированный список кортежей
        # [(Наименование, Количество, Цена), (Наименование, Количество, Цена), ...]
        # comp_table - отсортированный список списков
        # [[Наименование, Наименование ЕГАИС], [Наименование, Наименование ЕГАИС], ...]
        if not sold_goods or not comp_table:
            return []

        upd_sold_goods = []

        # Т.к. мы не можем гарантировать, что вложенные списки - списки из 2ух элементов,
        # то необходимо проверять их длину
        # Коммерческое наименование приводить нужно к нижнему регистру, т.к. в сервисе товар может храниться как
        # Aircraft - Рождественский Эль, а в таблице ЕГАИС как Aircraft - Рождественский эль
        temp_comp_table = {str(good[0]).lower(): good[1] for good in comp_table if len(good) > 1}
        for good in sold_goods:
            if str(good.commercial_name).lower() in temp_comp_table:
                upd_good = Good(good.commercial_name,
                                temp_comp_table[str(good.commercial_name).lower()],
                                good.quantity,
                                good.price)
            else:
                upd_good = good
            upd_sold_goods.append(upd_good)
            self.sold_goods_egais = sorted(upd_sold_goods)
        return self.sold_goods_egais

    def get_retail_demand_by_period_egais(self, start_period: datetime.datetime, end_period=None) -> list:
        """ Получение отсортированный список розничных продаж за определенный период, для списания в ЕГАИС
                :param start_period: начало запрашиваемого периода start_period 00:00:00
                :param end_period: конец запрашиваемого периода end_period 23:59:00. Если не указа,
                то считается, как start_period 23:59:00
                :return:
                    В случе успешного завершения возвращается список, элементов. Элемент - экземпляр класса Good
                        Наименование товара (str)
                        Количество проданного товара за заданный промежуток времени (float)
                        Стоимость единицы товара (float)
                    В случае ошибки возвращается пустой список.
                :rtype: list
                """
        if end_period is None:
            end_period = start_period

        self.logger.debug(f"Получаем список товаров из МС, проданных за период "
                          f"{(start_period.strftime('%Y-%m-%d 00:00:00'))} - "
                          f"{(end_period.strftime('%Y-%m-%d 23:59:00'))}")

        # Получаем список товаров из МС, проданных за период
        self.get_retail_demand_by_period(start_period)

        self.logger.debug(f"len(_sold_goods) = {len(self.sold_goods)}")

        if self.sold_goods:
            self.logger.debug(f"Получаем скорректированный список товаров, для списания в ЕГАИС")

            # Получаем скорректированный список товаров, для списания в ЕГАИС
            self._get_goods_for_egais(self.sold_goods)

            self.logger.debug(f"len(_sold_goods_egais) = {len(self.sold_goods_egais)}")

            if self.sold_goods_egais:

                self.logger.debug(f"Получаем доступ к Google API")
                gs = gs_class_lib.GoogleSheets()

                if gs.service is not None:
                    # получаем таблицу соответствий
                    compl_table_egais = gs.get_data(gs_vars.SPREEDSHEET_ID_EGAIS,
                                                    gs_vars.LIST_NAME_EGAIS,
                                                    f'{gs_vars.FIRST_CELL_EGAIS}:{gs_vars.LAST_COLUMN_EGAIS}2000')

                    if compl_table_egais:

                        self.logger.debug(f"Получили соответствие названий ЕГАИС: len(compl_table_egais) = "
                                          f"{len(compl_table_egais)}")
                        # соотносим проданные товары с наименованиями ЕГАИС
                        self._get_goods_compliance_egais(self.sold_goods, compl_table_egais)

        return self.sold_goods_egais

    def get_retail_demand_by_period(self, start_period: datetime.datetime, end_period=None) -> list:
        """ Получение списка розничных продаж за определенный период.
        :param start_period: начало запрашиваемого периода start_period 00:00:00
        :param end_period: конец запрашиваемого периода end_period 23:59:00. Если не указа, то считается,
        как start_period 23:59:00
        :return:
            В случе успешного завершения возвращается список, элементов. Элемент - экземпляр класса Good
                Наименование товара (str)
                Количество проданного товара за заданный промежуток времени (float)
                Стоимость единицы товара (float)
            В случае ошибки возвращается пустой список.
        :rtype: list
        """
        if not self._token:
            return []
        # если конец периода не указан входным параметром, считаем, что запросили продажи за вчера
        if end_period is None:
            end_period = start_period

        # формат даты документа YYYY-MM-DD HH:MM:SS
        date_filter_from = f'moment>{start_period.strftime("%Y-%m-%d 00:00:00")}'
        date_filter_to = f'moment<{end_period.strftime("%Y-%m-%d 23:59:00")}'

        headers = {
            'Content-Type': 'application/json',
            'Lognex-Pretty-Print-JSON': 'true',
            'Authorization': 'Bearer ' + self._token
        }
        # Т.к. в запрашиваемом периоде может оказаться продаж больше, чем 100, а МойСклад отдает только страницами
        # по 100 продаж за ответ, чтобы получить следующую страницу, нежно формировать новый запрос со смещением
        # offset=200, следующий offset-300 и т.д.
        need_request = True
        offset = 0
        # словарь в котором будем хранить список всех проданных товаров, за выбранный промежуток времени
        retail_demand_goods = {}
        response = None

        while need_request:
            # задаем фильтр
            request_filter = {
                'filter': [
                    f'organization={ms_urls.JSON_URL}entity/organization/{ms_urls.GEO_ORG_ID}',
                    date_filter_from,
                    date_filter_to
                ],
                'offset': {100 * offset},
                'expand': 'positions,positions.assortment',
                'limit': '100'
            }

            try:
                response = requests.get(urljoin(ms_urls.JSON_URL, 'entity/retaildemand'), request_filter,
                                        headers=headers)
                response.raise_for_status()
            except requests.RequestException as error:
                self.logger.exception(f"Не удалось получить продажи из сервиса MoySklad: {error.args[0]}")
                return []  # возвращаем пустой список

            # Проверяем получили ли в ответе не пустой список продаж response.json()['meta']['size'] - размер массива
            # в ответе len(response.json()['rows']) - размер массива в ответе, если это число меньше,
            # чем response.json()[ 'meta']['size'] то надо будет делать дополнительные запросы со смещением 100
            # словарь для хранения списка проданных товаров. Ключ - наименование, значение - список [количество
            # товара, цена]

            # Смотрим, вернулись ли нам данные в ответе
            # если в ответе есть данные
            if response.json()['meta']['size'] > 0:
                # проверяем нужно ли будет делать еще один запрос
                if len(response.json()['rows']) < 100:
                    need_request = False
                # если нужно будет делать еще один запрос
                else:
                    offset += 1
            else:
                return []
        # проходим по всем продажам и заполняем список с товарами
        for sale in response.json()['rows']:
            for sale_position in sale['positions']['rows']:
                # проверяем наличие товара в словаре
                if sale_position['assortment']['name'] in retail_demand_goods:
                    # увеличиваем счетчик проданного товара
                    retail_demand_goods[sale_position['assortment']['name']][0] += sale_position['quantity']
                else:
                    # добавляем товар в словарь проданных товаров
                    retail_demand_goods[sale_position['assortment']['name']] = [sale_position['quantity'],
                                                                                sale_position['price'] / 100]

        self.sold_goods = sorted([Good(key, '', values[0], values[1]) for key, values in retail_demand_goods.items()])
        return self.sold_goods

    def _get_goods_for_egais(self, goods: list) -> list:
        """ Метод удаляет из входного списка товаров, наименования перечисленные в файле moysklad_exclude_goods.txt
                :param goods: Список товаров. Если передаваемый список - многомерный массив, то наименованием считается
                0ой элемент, вложенного элемента list[i][0]
                :return:
                    В случе успешного завершения возвращается список, элементов
                    В случае ошибки возвращается пустой список.
                :rtype: list
         """
        # список слов исключений
        exclude_words = set()

        if goods:
            self.logger.debug(f"Входной список товаров: len(goods) = {len(goods)}")
        else:
            self.logger.error(f"Входной список товаров пустой: len(goods) = {len(goods)}")
            return []

        if goods:

            exclude_file_name = os.path.join(os.path.dirname(__file__), 'moysklad_exclude_goods.txt')
            self.logger.debug(
                f"Открываем файл исключений: {exclude_file_name}")
            try:
                # заполняем список слов исключений
                with open(exclude_file_name, 'r', encoding='utf-8') as file:
                    for line in file:
                        if not (line[0] in ['#', '', ' ', '\n']):
                            exclude_words.add(line.replace('\n', '').lower())
            except FileNotFoundError:
                # запись в лог, файл не найден
                self.logger.exception(f"Не удалось открыть файл исключений")
                return []

        if goods:
            # убираем из списка товаров, товары которые попадают в список исключений
            i = 0
            while i < len(goods):
                # if goods[i][0].lower().find('варниц') != -1:
                #     a = -1
                for exclude_word in exclude_words:
                    # Если список товаров передан списком кортежей [(Наименование, количество, цена), ... ]
                    if goods[i].commercial_name.lower().find(exclude_word.lower()) != -1:
                        goods.pop(i)
                        i -= 1
                # убираем из наименования товара все что содержится в скобках (OG, ABV, ..)
                goods[i] = Good(goods[i].commercial_name.split(' (')[0].replace('  ', ' ').strip(),
                                goods[i].egais_name,
                                goods[i].quantity,
                                goods[i].price)

                # goods[i] = (goods[i][0].split(' (')[0], goods[i][1], goods[i][2])
                i += 1

        self.sold_goods_egais = sorted(goods)
        return self.sold_goods_egais


if __name__ == '__main__':
    ms = MoySklad()
    ms.get_token()

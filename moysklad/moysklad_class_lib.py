""" В модуле хранится описание классов.

"""
import requests
import os, sys
import logging
import logging.config
import logger_config
import project_settings

sys.path.insert(1, project_settings.PROJECT_PATH)

import moysklad.moysklad_privatedata as ms_pvdata
import moysklad.moysklad_lib as ms_lib
import moysklad.moysklad_urls as ms_urls



class MoySklad(object):
    """ Класс описывает работу с сервисом МойСклад"""
    token = ''  # токен для работы с сервисом
    logger = None

    def __init__(self):
        try:
            self.token = ms_lib.get_access_token(ms_pvdata.USER, ms_pvdata.PASSWORD)
            logging.config.dictConfig(logger_config.LOGGING_CONF)
            self.logger = logging.getLogger("moysklad")
        except Exception as error:
            logger.exception(f"Не удалось создать инстанс MoySklad")


    def get_goods_compliance_egais(self, sold_goods: list, comp_table: list):
        """
        Метод сранивает два списка sold_goods и comp_table, возвращает новый sold_goods, c заполнеными наименованиями ЕГАИС
        :param sold_goods:
        :param comp_table:
        :return:
        """
        # sold_goods - отсортированый список кортежей
        # [(Наименование, Количество, Цена), (Наименование, Количество, Цена), ...]
        # comp_table - отсортированый список списков
        # [[Наименование, Наименование ЕГАИС], [Наименование, Наименование ЕГАИС], ...]
        if len(sold_goods) == 0 or len(comp_table) == 0:
            return []
        upd_sold_goods =[]
        try:
            for sold_good in sold_goods:
                # if str(sold_good[0]) == 'План Б - Parhelion' or str(sold_good[0]) == 'Aircraft - Шоколадный Стаут':
                #     # Aircraft - Шоколадный Стаут
                #     a = -1
                start_ind = 0
                end_ind = len(comp_table) - 1
                mid_ind = len(comp_table) // 2
                # бинарный поиск
                while str(comp_table[mid_ind][0]).lower() != str(sold_good[0]).lower() and start_ind < end_ind:
                    if sold_good[0] > comp_table[mid_ind][0]:
                        start_ind = mid_ind + 1
                    else:
                        end_ind = mid_ind - 1
                    mid_ind = (start_ind + end_ind) // 2
                else:
                    # если нашли совпадение
                    if str(sold_good[0]).lower() == str(comp_table[mid_ind][0]).lower():
                        # заполняем результиуреющий список проаданных товаров в формате
                        # (Комерческое_наименование, ЕГАИС наименование, Количество, Цена)
                        upd_sold_goods.append((sold_good[0], comp_table[mid_ind][1], sold_good[1], sold_good[2]))
                    # если совпадение не найдено
                    else:
                        upd_sold_goods.append((sold_good[0], '', sold_good[1], sold_good[2]))
            return upd_sold_goods
        except Exception as error:
            return []

    def get_retail_demand_by_period(self, start_period: str, end_period: str) -> list:
        """ Получение списка розничных продаж за определенный период
        :param start_period: начало запрашиваемого периода YYYY-MM-DD HH:MM:SS
        :param end_period: конец запршиваемого периода YYYY-MM-DD HH:MM:SS
        :return:
            В случе успешного заврешения возвращается список, элементов
                Наименование товара (str)
                Количество продаанного товара за заданный промежуток времени (float)
                Стоимость еденицы товара (float)
            В случае ошибки возвращаеься пустой список
        :rtype: list
        """
        if self.token == '' or start_period == '' or end_period == '':
            return []

        # формат даты документа YYYY-MM-DD HH:MM:SS
        date_filter_from = 'moment>' + start_period
        date_filter_to = 'moment<' + end_period
        # date_filter_from = 'moment>' + '2021-10-13 00:00:00'  # дата, с которой запрашиваем
        # date_filter_to = 'moment<' + '2021-10-18 23:59:00'  # дата, до которой запрашиваем

        headers = {
            'Content-Type': 'application/json',
            'Lognex-Pretty-Print-JSON': 'true',
            'Authorization': 'Bearer ' + self.token
        }
        # т.к. в запрашиваеммом периоде может оказатся продаж болше, чем 100, а МойСклад отдает только страницамми
        # по 100 продаж за ответ, чтобы получить следующую страницу, нежно формировать новый запрос с смещением
        # offset=200, следующий offset-300 и т.д.
        need_request = True
        offset = 0
        # словарь в котором будем хранить список всех проданных товаров, за выбранный промежуток времени
        retail_demand_goods = {}

        try:
            while need_request:
                # задаем фильтр
                request_filter = f'?filter=organization={ms_urls.JSON_URL}entity/organization/{ms_urls.GEO_ORG_ID}' \
                                 f'&filter={date_filter_from}&filter={date_filter_to}&offset={100 * offset}'
                response = requests.request("GET", ms_urls.JSON_URL + 'entity/retaildemand' + request_filter +
                                            '&expand=positions,positions.assortment&limit=100', headers=headers)

                response.raise_for_status()

                # проверяем получили ли в ответе не пустой список продаж response.json()['meta']['size'] - размер массива в
                # ответе len(response.json()['rows']) - размер массива в ответе, если это число меньше, чем response.json()[
                # 'meta']['size'] то надо будет делать доплнительные запросы с смещением 100
                # словарь для хранения списка прданных товаров. Ключ - наименование, значен - список [количество товара, цена]

                # Смотрим вернулись ли нам данные в ответе
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
            return [(key, values[0], values[1]) for key, values in retail_demand_goods.items()]

        except requests.RequestException as error:
            return []  # возвращаем ошибку
        except Exception as error:
            return []  # возвращаем ошибку

    def get_goods_for_egais(self, goods: list) -> list:
        """ Метод удаляет из входного списка товаров, наменования перечисленные в файле moysklad_exclude_goods.txt
                :param goods: Список товаров. Если передаваемый список - многомерный массив, то наименованием считатется
                0ой элемент, вложенного элемента list[i][0]
                :return:
                    В случе успешного заврешения возвращается список, элементов
                    В случае ошибки возвращаеься пустой список
                :rtype: list
         """
        unsuccess = False

        # список слов исключений
        exclude_words = []
        try:
            if len(goods) == 0:
                self.logger.error(f"Входной список товаров пустой: len(goods) = {len(goods)}")
                unsuccess = True
            else:
                self.logger.debug(f"Входной список товаров: len(goods) = {len(goods)}")

            if not unsuccess:
                self.logger.debug(f"Открывем файл исключений: {project_settings.PROJECT_PATH}/moysklad/moysklad_exclude_goods.txt")

                # заполняем список слов исключений
                with open(project_settings.PROJECT_PATH + '/moysklad/moysklad_exclude_goods.txt', 'r', encoding='utf-8') as file:
                    for line in file:
                        if not (line[0] in ['#', '', ' ', '\n']):
                            exclude_words.append(line.replace('\n', '').lower())
                exclude_words = list(set(exclude_words))

            if not unsuccess:
                # убираем из списка товаров, товары которые попадают в список исключений
                i = 0
                while i < len(goods):
                    # if goods[i][0].lower().find('варниц') != -1:
                    #     a = -1
                    for j in range(len(exclude_words)):
                        # если список товаров передан списком кортежей [(Наименование, количество, цена), ... ]
                        if goods[i][0].lower().find(exclude_words[j].lower()) != -1:
                            goods.pop(i)
                            i -= 1
                    # убираем из наименования товара все что содержится в скобках (OG, ABV, ..)
                    goods[i] = (goods[i][0].split(' (')[0], goods[i][1], goods[i][2])
                    i += 1

            return sorted(goods)
        except FileNotFoundError:
            # запись в лог, файл не найден
            self.logger.exception(f"Не удалось открыть файл исключений")
            return []
        except Exception as error:
            self.logger.exception(f"Ошибка: " + error)
            return []  # возвращаем ошибку
"""В модуле хранятся url'ы и функции, для доступа в сервис MoySklad https://www.moysklad.ru/ по API."""

import base64
from datetime import datetime
from enum import Enum
from typing import Dict, Any, NamedTuple
from urllib.parse import urljoin

import privatedata.moysklad_privatedata as ms_pvdata

JSON_URL = 'https://online.moysklad.ru/api/remap/1.2/'  # ссылка для подключения к МС по JSON API 1.2
BEER_FOLDER_ID = '8352f575-b4c1-11e7-7a34-5acf0009a77f'  # id папки "Пиво"
GEO_ORG_ID = '0a405989-b28a-11e7-7a31-d0fd00338283'  # id юр. лица "География"
GEO_ORG_HREF = JSON_URL + 'entity/organization/' + GEO_ORG_ID  # Ссылка на юр. лицо "География"
GEO_SHOP_ID = '5057e2b5-b498-11e7-7a34-5acf0002684b'  # d розничной точки "География"
GEO_SHOP_HREF = JSON_URL + 'entity/retailstore/' + GEO_SHOP_ID


class UrlType(Enum):
    """Перечисление для определения, какой тип url необходимо сформировать.

    token - для получения токена.
    retail_demand - для получения розничных продаж
    """

    token = 1
    retail_demand = 2


class Url(NamedTuple):
    """Класс для описания запроса в сервис МойСклад."""

    url: str  # url для запроса в сервис
    request_filter: Dict[str, Any]  # словарь для фильтров


def get_headers(token: str = '') -> Dict[str, Any]:
    """Метод получения словаря заголовков для передачи в запросе к сервису МойСклад.

    :return:
        Если token пустой, то возвратится словарь для запроса token.
        Если не пустой возвратиться словарь для запросов сущностей МойСклад
    """
    _headers: Dict[str, Any]
    if token:
        _headers = {
            'Content-Type': 'application/json',
            'Lognex-Pretty-Print-JSON': 'true',
            'Authorization': 'Bearer ' + token}
    else:
        pvd = f'{ms_pvdata.USER}:{ms_pvdata.PASSWORD}'.encode()
        _headers = {'Authorization': f'Basic{base64.b64encode(pvd)}'}
    return _headers


def get_url(_type: UrlType, start_period: datetime = datetime.today(), end_period: datetime = None) -> Url:
    """Функция для получения url.

    :param _type: UrlType.token - url для получения токена, UrlType.retail_demand - url для получения розничны
    продаж за определённый период
    :param start_period: начало периода продаж
    :type start_period: datetime.datetime
    :param end_period: конец периода продаж. Если не указан, считается как start_period 23:59
    :type start_period: datetime.datetime

    :returns: Возвращается объект Url
    :rtypes: Url
    """
    # если нужен url для запроса токен
    if _type == UrlType.token:
        # формируем url для запроса токена
        url = Url(urljoin(JSON_URL, 'security/token'), {})

    # если нужен url для запроса продаж
    elif _type == UrlType.retail_demand:
        # если конец периода не указан входным параметром, считаем, что запросили продажи за вчера
        if end_period is None:
            end_period = start_period

        # формат даты документа YYYY-MM-DD HH:MM:SS
        date_filter_from = f'moment>{start_period.strftime("%Y-%m-%d 00:00:00")}'
        date_filter_to = f'moment<{end_period.strftime("%Y-%m-%d 23:59:00")}'

        # Т.к. в запрашиваемом периоде может оказаться продаж больше, чем 100, а МойСклад отдает только страницами
        # по 100 продаж за ответ, чтобы получить следующую страницу, нежно формировать новый запрос со смещением
        # offset=200, следующий offset-300 и т.д. В данной реализации это не учтено, т.к. больше 100 продаж не выявлено
        request_filter: dict[str, Any] = {
            'filter': [
                f'organization={JSON_URL}entity/organization/{GEO_ORG_ID}',
                f'assortment={JSON_URL}entity/productfolder/{BEER_FOLDER_ID}',
                date_filter_from,
                date_filter_to],
            'offset': '0',
            'expand': 'positions,positions.assortment',
            'limit': '100'}
        url = Url(urljoin(JSON_URL, 'entity/retaildemand'), request_filter)
    else:
        url = Url('', {})
    return url

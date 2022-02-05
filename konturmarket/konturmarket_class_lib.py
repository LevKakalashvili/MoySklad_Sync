"""В модуле описаны классы для работы с сервисом Контур.Маркет https://market.kontur.ru/."""
import json
from dataclasses import dataclass
from typing import List, Tuple, Optional

import privatedata.kontrurmarket_privatedata as km_pvdata
import requests
from pydantic import BaseModel, Field

from konturmarket.konturmarket_urls import Url, UrlType, get_url

session = requests.Session()


class Brewery(BaseModel):
    """Клас описывает структуру компании производителя, продукции в соответствии с терминами ЕГАИС. Словарь
    'producer' в JSON представлении."""

    name: str = Field(alias='shortName')


class GoodEGAIS(BaseModel):
    """Клас описывает структуру товара, продукции в соответствии с терминами ЕГАИС.
    Словарь 'productInfo' в JSON представлении."""

    # ЕГАИС наименование
    name: str = Field(alias='fullName')

    # Код алкогольной продукции (код АП) в ЕГАИС. Уникальный 19-ти значный код. Если значащих цифр в
    # коде меньше 19-ти, то вперед дописываются нули. Это при строковом представлении
    alco_code: str = Field(alias='egaisCode')

    # Емкость тары. Необязательный параметр. Отсутствие этого параметра говорит о том, что товар разливной
    capacity: Optional[float] = None

    # Описание производителя
    brewery: Brewery = Field(alias='producer')

    def to_tuple(self) -> Tuple[str, str, str]:
        """Метод возвращает кортеж вида (ЕГАИС_НАИМЕНОВАНИЕ, ЕГАИС_КОД)."""
        return self.name, self.alco_code, self.brewery.name

    def get_description(self):
        return (
            f'Пивоварня: {self.brewery.name}  '
            f'Наименование: {self.name}  '
            f'Код: {self.alco_code}  '
        )


@dataclass()
class KonturMarket:
    """Класс описывает работу с сервисом Контур.Маркет https://market.kontur.ru/."""

    # Переменная устанавливается в True, в случае успешного логина в сервисе
    connection_OK: bool = False

    @staticmethod
    def get_egais_assortment() -> List[GoodEGAIS]:
        """Метод возвращает список инстансов GoodEGAIS, полученных из сервиса."""

        url: Url = get_url(UrlType.egais_assortment)
        response = session.get(url.url)

        goods = dict(response.json()).get('list')
        # Если получили успешный ответ и есть список товаров
        if response.ok and goods:
            goods_list: List[GoodEGAIS]
            # Проходим по всему списку товаров, наименований.
            for good in goods:
                # Получаем словарь с информацией о товаре
                goods_list.append(GoodEGAIS(**good['productInfo']))

            # Сортировка по названию пивоварни
            goods_list = sorted(goods_list, key=lambda element: element.brewery.name)
            return goods_list
        else:
            return []

    def login(self) -> bool:
        auth_data = {
            'Login': km_pvdata.USER,
            'Password': km_pvdata.PASSWORD,
            'Remember': False,
        }
        # auth_data = '{"Login":"kakalashvililev@yandex.ru","Password":"340354Lev!","Remember":false}'
        # Пытаемся залогиниться на сайте
        url: Url = get_url(UrlType.login)
        response = session.post(
            url=url.url,
            data=json.dumps(auth_data),
            headers=url.headers,
            cookies=url.cookies,
        )
        self.connection_OK = response.ok

        return response.ok


# Создаем инстанс сервиса
kmarket = KonturMarket()
kmarket.login()

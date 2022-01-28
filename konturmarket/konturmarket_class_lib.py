"""В модуле описаны классы для работы с сервисом Контур.Маркет https://market.kontur.ru/"""
import json
from dataclasses import dataclass
from pydantic import BaseModel, Field

from typing import List, Tuple

import requests

from konturmarket_urls import Url, UrlType, get_url
import privatedata.kontrurmarket_privatedata as km_pvdata

session = requests.Session()


class GoodEGAIS(BaseModel):
    """Клас описывает структуру товара, продукции в соответствии с терминами ЕГАИС"""
    # ЕГАИС наименование
    name: str = Field(alias='fullName')

    # Код алкогольной продукции (код АП) в ЕГАИС. Уникальный 19-ти значный код. Если значащих цифр в
    # коде меньше 19-ти, то вперед дописываются нули. Это при строковом представлении
    alco_code: str = Field(alias='egaisCode')

    def to_tuple(self) -> Tuple[str, str]:
        """Метод возвращает кортеж вида (ЕГАИС_КОД, ЕГАИС_НАИМЕНОВАНИЕ)."""
        return (self.alco_code, self.name)


@dataclass()
class KonturMarket:
    """Класс описывает работу с сервисом Контур.Маркет https://market.kontur.ru/"""

    @staticmethod
    def login() -> bool:
        auth_data = {
            'Login': km_pvdata.USER,
            'Password': km_pvdata.PASSWORD,
            'Remember': False
        }
        # auth_data = '{"Login":"kakalashvililev@yandex.ru","Password":"340354Lev!","Remember":false}'
        # Пытаемся залогиниться на сайте
        url: Url = get_url(UrlType.login)
        response = session.post(
            url=url.url,
            data=json.dumps(auth_data),
            headers=url.headers,
            cookies=url.cookies
        )
        return response.ok

    @staticmethod
    def get_egais_assortment() -> List[GoodEGAIS]:
        goods_list: List[GoodEGAIS] = list()

        url: Url = get_url(UrlType.egais_assortment)
        response = session.get(url.url)

        goods = dict(response.json()).get('list')
        # Если получили успешный ответ и есть список товаров
        if response.ok and goods:
            # Проходим по всему списку товаров, наименований.
            for good in goods:
                # Получаем словарь с информацией о товаре
                goods_list.append(GoodEGAIS(**good['productInfo']))
            return goods_list
        else:
            return []

""" В модуле хранятся url'ы для доступа в сервис MoySklad https://www.moysklad.ru/ по API.

"""

JSON_URL = 'https://online.moysklad.ru/api/remap/1.2/'  # ссылка для подключения к МС по JSON API 1.2
BEER_FOLDER_ID = "8352f575-b4c1-11e7-7a34-5acf0009a77f"  # id папки "Пиво"
GEO_ORG_ID = '0a405989-b28a-11e7-7a31-d0fd00338283'  # id юр. лица "География"
GEO_ORG_HREF = JSON_URL + 'entity/organization/' + GEO_ORG_ID  # ссылка на юр. лицо "География"
GEO_SHOP_ID = '5057e2b5-b498-11e7-7a34-5acf0002684b'  # d розничной точки "География"
GEO_SHOP_HREF = JSON_URL + 'entity/retailstore/' + GEO_SHOP_ID


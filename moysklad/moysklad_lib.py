""" В модуле хранятся функции для работы в сервисе MoySklad https://www.moysklad.ru/ по API.

"""
import base64  # pip install pybase64
import requests  # pip install requests
import moysklad.moysklad_urls as moy_sklad_urls


def get_access_token(user: str, pswd: str) -> str:
    """ Получение токена для доступа и работы с МС по JSON API 1.2.

        При успешном ответе возвращаем токен, в случае ошибок ''
    """

    # определяем заголовок
    headers = {
        'Authorization': 'Basic' + str(base64.b64encode((user + ':' + pswd).encode()))
    }
    # отправляем запрос в МС для получения токена
    try:
        response = requests.request("POST", moy_sklad_urls.JSON_URL + 'security/token', headers=headers)
        response.raise_for_status()
    except requests.RequestException as error:
        return ''  # возвращаем пустую строку
    except Exception as error:
        return ''  # возвращаем пустую строку
    try:
        access_token = response.json()['access_token']  # возвращаем токен
        return access_token  # возвращаем токен
    except Exception as error:
        return ''  # возвращаем пустую строку

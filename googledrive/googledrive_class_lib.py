"""
Модуль для работы с Google Sheets
"""
import googleapiclient.discovery  # pip install google-api-python-client
import httplib2  # pip install httplib2
from oauth2client.service_account import ServiceAccountCredentials
import googledrive.googlesheets_vars as gs_vars
import os
import logging.config
import logger_config

# pip install google-api-python-client библиотека для работы с googlу api
# pip install oauth2client библиотека для авторизации


class GoogleSheets:
    """ Класс методы для чтения данных из Google Sheets"""

    def __init__(self) -> None:
        logging.config.dictConfig(logger_config.LOGGING_CONF)
        self.logger = logging.getLogger("google")

        self.service = None # сервисный объект для работы с Google API
        self.get_access()

    def get_access(self) -> bool:
        """Метод получения доступа сервисного объекта Google API
        :return: Возвращает True если получилось подключиться к Google API, False в противном случае
        """
        # Авторизуемся и получаем service — экземпляр доступа к API
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            # все приватные данные храним в папке /MoySklad_Sync/privatedata
            os.path.join(os.path.dirname(os.path.dirname(__file__)),  # путь до /privatedata
                         'privatedata',
                         gs_vars.CREDENTIALS_FILE),
            [gs_vars.SPREEDSHEETS_URL, gs_vars.GDRIVE_URL])
        http_auth = credentials.authorize(httplib2.Http())
        try:
            self.service = googleapiclient.discovery.build('sheets', 'v4', http=http_auth)
            self.logger.debug(f"Получили доступ к Google API")
            return True
        except Exception as e:
            self.logger.error(f"Не удалось создать сервисный объект для работы с Google API: {e.args[0]}")
            return False

    def get_data(self, spreadsheets_id: str, list_name: str, list_range: str) -> list:
        """
        :param spreadsheets_id: id таблицы в Google Sheets
        :param list_name: текстовое имя листа
        :param list_range: запрашивемый диапазон A1:H100
        :return: Возвращает список списков [[], []..]. Каждый элемент списка - список из 2 элементов. 1 - коммерческое
                название, 2 - наименование ЕГАИС. Пустой список в случае не удачи
        """
        if not spreadsheets_id or not list_name or not list_range:
            return []

        values = self.service.spreadsheets().values().get(
            spreadsheetId=spreadsheets_id,
            range=f'{list_name}!{list_range}',
            majorDimension='ROWS'
            ).execute()

        if not values['values']:
            return []

        # гуглшит отдает диапазон, отсекая в запрашиваемом диапазоне пустые ячейки снизу, но пустые строки
        # могут оказаться в середине текста
        # отсоритруем, чтобы пустые строки оказались в верху, а потом удалим их
        values = sorted(values['values'])
        i = 0
        while not values[i]:
            i += 1
        return values[i:]

if __name__ == '__main__':
    gs = GoogleSheets()
"""
Модуль для работы с Google Sheets
"""
import googleapiclient.discovery  # pip install google-api-python-client
import httplib2  # pip install httplib2
from oauth2client.service_account import ServiceAccountCredentials
import googledrive.googlesheets_vars as gs_vars
import os

# pip install google-api-python-client библиотека для работы с googlу api
# pip install oauth2client библиотека для авторизации


class GoogleSheets(object):
    """ Класс описывает работу с Google Sheets"""
    service = None

    def __init__(self) -> object:
        self.get_access()

    def get_access(self) -> int:
        # Авторизуемся и получаем service — экземпляр доступа к API
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            os.path.dirname(__file__) + '/' + gs_vars.CREDENTIALS_FILE,
            ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        http_auth = credentials.authorize(httplib2.Http())
        self.service = googleapiclient.discovery.build('sheets', 'v4', http=http_auth)

        # проверяме получилось ли получить экземпляр сервиса
        if self.service is not None:
            return 0
        else:
            return -1

    def get_data(self, spreadsheets_id: str, list_name: str, list_range: str) -> list:
        """

        :param spreadsheets_id: id таблицы в Google Sheets
        :param list_name: имя, тестковое, листа
        :param list_range: запрашивемый диапазон A1:H100
        :return: Возвращает список списков [[], []..]. Каждый элеемнт списка список из 2 элементов. 1 - коммерческое
                название, 2 - наименование ЕГАИС
        """
        if spreadsheets_id == '' or list_name == '' or list_range == '' and not (self.service is None):
            return []

        try:
            values = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheets_id, range=list_name + '!' + list_range, majorDimension='ROWS'
            ).execute()
            # гуглшит отдает дапазон, отсекая в запрашиваемом диапазоне пустые ячейки снизу. но пустые строки могут
            # могут оказаться посередине текста
            # отсоритруем, чтобы пустые строки оказались в верху, а потом удалим их
            values = sorted(values['values'])
            i = 0
            # убираем пустые списки
            while i < len(values):
                if len(values[i]) == 0:
                    i += 1
                else:
                    break
            return values[i:]
        except Exception as error:
            error.error_details
            return []

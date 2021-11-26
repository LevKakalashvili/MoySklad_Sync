""" В модуле раняться данны для доступа к Google по API.

"""
# сервисный аккаунт google account@moyskald-sync.iam.gserviceaccount.com для работы по API

# Файл, полученный в Google Developer Console
CREDENTIALS_FILE = 'googledrive_credentials.json'

# ID Google Sheets документа (можно взять из его URL)
SPREESHEET_ID_GOODS_AVAILABILITY = '1Sa4MSpj04288-UScp2t8_5vpZgSYmLrauf-OD3i-8O0'  # таблица "Наличие"
LIST_ID_GOODS_AVAILABILITY = '96547513'  # лист "Остаток" в таблице "Наличие"
LIST_NAME_GOODS_AVAILABILITY = 'Актуальное наличие'  # лист "Остаток" в таблице "Наличие"
FIRST_CELL_GOODS_AVAILABILITY = 'A2'  # первая ячейка с данными в таблице "Наличие"
LAST_COLUMN_GOODS_AVAILABILITY = 'G'  # последний столбец с данными в таблице "Наличие"

SPREESHEET_ID_EGAIS = '1xY9W8a9fPazRW1Nc_K-5CkEwm4Q28jtsv_t2-Z0tiAE'
LIST_ID_EGAIS = '0'
LIST_NAME_EGAIS = 'Соответсвия ЕГАИС'
FIRST_CELL_EGAIS = 'B2'
LAST_COLUMN_EGAIS = 'C'

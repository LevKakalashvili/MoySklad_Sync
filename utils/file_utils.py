"""Модуль для работы с файлами. Сохранение данных в файл, удаление файлов."""
import datetime
import os
from typing import Any, List

import pandas as pd

import moysklad.moysklad_class_lib as ms_class_lib


def remove_file(file_name: str) -> None:
    """Функция удаления файла."""
    if file_name != '' and os.path.isfile(file_name):
        os.remove(file_name)


def save_to_excel(file_name: str, data: list[ms_class_lib.Good], date: datetime.datetime, add_date: bool = True) -> str:
    """Функция сохранения в файл excel.

    :param file_name: Имя файла.
    :param data: Таблица для сохранения.
    :param date: Дата, которая добавляется к имени файла.
    :param add_date: По умолчанию True - к имени файла будет добавлена текущая дата (ИМЯ_ФАЙЛА_ГОД_МЕСЯЦ_ДЕНЬ)
    :return: Имя файла
    """
    if not data:
        return ''

    if add_date:
        file_name = f'{file_name}_{str(date.date())}.xlsx'

    # В конечном итоге мне нужен именно excel, т.к. продавцы, которые пользуют сервис, скачивают файл из телеги,
    # люди не далекие. Открыть Excel они могут, а вот делать доп. действия с csv будет сложно объяснить и инструкции
    # тут не помогут.
    # Да, ставить pandas, и делать DataFrame для этих целей не очень-то целесообразно. Но меня устроила компактность
    # кода.

    # пишем данные в файл

    df = pd.DataFrame(data)
    df.to_excel(file_name, sheet_name='Списания ЕГАИС', index=False, header=False)
    return file_name


def save_to_txt(file_name: str, data: list[Any], add_date: bool = True) -> str:
    """Функция сохранения в текстовый файл."""
    if not data:
        return ''

    if add_date:
        file_name = f'{file_name}_{str(datetime.datetime.now().date() - datetime.timedelta(days=1))}.txt'

        # пишем данные в файл
        with open(file_name, 'w', encoding='utf-8') as f:
            for line in data:
                line_ = ''.join(str(line))
                f.write(line_ + '\n')

    return file_name


def read_file_txt(file_name: str) -> list[str]:
    """Метод возвращает список строк прочитанных из файла.

    :param file_name: Имя открываемого файла
    :return: Список строк из файла file_name
    """
    if not file_name:
        return []

    exclude_words: List[str] = []

    try:
        # self.logger.debug(f'Открываем файл исключений: {file_name}')
        # заполняем список слов исключений
        with open(file_name, 'r', encoding='utf-8') as file:
            for line in file:
                if not (line[0] in ['#', '', ' ', '\n']):
                    set(exclude_words).add(line.replace('\n', '').lower())
        return exclude_words
    except FileNotFoundError:
        # self.logger.debug(f'Не найден файл исключений: {file_name}')
        return []

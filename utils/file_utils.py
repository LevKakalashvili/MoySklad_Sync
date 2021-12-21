import datetime
import os

import pandas as pd

import moysklad.moysklad_class_lib as ms


def remove_file(file_name: str) -> None:
    if file_name != '' and os.path.isfile(file_name):
        os.remove(file_name)


def save_to_excel(file_name: str, data: list[ms.Good], add_date: bool = True) -> str:
    """
     Функция сохранения в файл excel
    :param file_name:
    :param data: Таблица для сохранения
    :param add_date: По умолчанию True - к имени файла будет добавлена текущая дата (ИМЯ_ФАЙЛА_ГОД_МЕСЯЦ_ДЕНЬ)
    :return: Имя файла
    """

    if not data:
        return ''

    if add_date:
        file_name = f'{file_name}_{str(datetime.datetime.now().date() - datetime.timedelta(days=1))}.xlsx'

    # В конечном итоге мне нужен именно excel, т.к. продавцы, которые пользуют сервис, скачивают файл из телеги,
    # люди не далекие. Открыть Excel они могут, а вот делать доп. действия с csv будет сложно объяснить и инструкции
    # тут не помогут.
    # Да, ставить pandas, и делать DataFrame для этих целей не очень-то целесообразно. Но меня устроила компактность
    # кода.

    # пишем данные в файл

    df = pd.DataFrame(data)
    df.to_excel(file_name, sheet_name='Списания ЕГАИС', index=False, header=False)
    return file_name


def save_to_txt(file_name: str, data: list[ms.Good], add_date: bool = True) -> str:

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

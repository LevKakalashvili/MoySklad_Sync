import os
import pandas as pd
import datetime



def remove_file(file_name: str):
    try:
        if file_name != '' and os.path.isfile(file_name):
            os.remove(file_name)
    except Exception as error:
        pass

def save_to_excel(file_name: str, data: list, add_date=True) -> str:
    """
    Функция сохранения в файл excel
    :param file_name:
    :param data:
    :param add_date:
    :return: Имя файла
    """
    if len(data) == 0:
        return ''
    try:
        if add_date:
            new_file_name = file_name + '_' + str(datetime.datetime.now().date() - datetime.timedelta(days=1)) + '.xlsx'
            remove_file_name = file_name + '_' + \
                               str(datetime.datetime.now().date() - datetime.timedelta(days=2)) + '.xlsx'
        else:
            remove_file_name = ''
        # пишем данные в файл
        df = pd.DataFrame(data)
        df.to_excel(new_file_name, sheet_name='Списания ЕГАИС', index=False, header=False)
        return new_file_name

    except Exception as error:
        return ''


def save_to_txt(file_name: str, data: list, add_date=True) -> int:
    """ Сохранение в текстовый файл"""
    if len(data) == 0:
        return -1
    try:
        if add_date:
            new_file_name = file_name + '_' + str(datetime.datetime.now().date() - datetime.timedelta(days=1)) + '.txt'
            remove_file_name = file_name + '_' + \
                               str(datetime.datetime.now().date() - datetime.timedelta(days=2)) + '.txt'
        else:
            new_file_name = file_name + '.txt'
            remove_file_name = ''
        # пишем данные в файл
        f = open(new_file_name, 'w', encoding="utf-8")
        for line in data:
            line_ = ''.join(str(line))
            f.write(line_ + '\n')
        f.close()
        # удаляем "вчерашний" файл
        if remove_file_name != '' and os.path.isfile(remove_file_name):
            os.remove(remove_file_name)
    except Exception as error:
        return -1

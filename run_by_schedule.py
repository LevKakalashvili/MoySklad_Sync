"""Модуль для запуска сервиса по расписанию."""
import privatedata.tbot_privatedata as pvd_telebot

import utils.service as service

if __name__ == '__main__':
    # Отправка заполненного файла с продажами за сегодня в телеграм чат
    service.send_sales_file_to_telegram(pvd_telebot.TELEGRAM_GEO_CHAT_ID)

    # Обновление таблицы GoogleSheets новым списком ЕГАИС наименований
    service.update_goooglesheets_egais_assortment(pvd_telebot.TELEGRAM_GEO_CHAT_ID)

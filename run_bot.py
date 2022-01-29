"""Модуль для запуска бота Telegram."""
import tbot.tbot as telegram_bot


if __name__ == '__main__':
    telegram_bot.run()

# Запуск в фоне на сервере.
# sudo python3 /var/geo/MoySklad_Sync/run_bot.py &

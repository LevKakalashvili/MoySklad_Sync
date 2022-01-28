"""Модуль для запуска синхронизации Контур.Маркета с БД"""
from typing import List
from konturmarket_class_lib import KonturMarket, GoodEGAIS


if __name__ == "__main__":
    kmarket = KonturMarket()
    # Если залогинились.
    if kmarket.login():
        egais_goods: List[GoodEGAIS] = kmarket.get_egais_assortment()

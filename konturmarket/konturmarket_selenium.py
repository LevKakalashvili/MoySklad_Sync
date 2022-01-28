import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from typing import Dict
from enum import Enum

from konturmarket.konturmarket_urls import EGAIS_ASSORTMENT_URL
from privatedata.kontrurmarket_privatedata import USER, PASSWORD
from konturmarket_class_lib import GoodEGAIS


class Browser(Enum):
    Chrome = 0
    Firefox = 1


# Режим тестирования.
DEBUG = True
# Задержка перед поиском элемента на странице действиями на странице.
TIMEOUT = 2
# Количество отображаемых строк в таблице на страницке в товаров.
AMOUNT_GOODS_ON_PAGE = 30
BROWSER = Browser.Chrome

if BROWSER == Browser.Firefox:
    options = webdriver.FirefoxOptions()
else:
    options = webdriver.ChromeOptions()
    # https://stackoverflow.com/questions/55072731/selenium-using-too-much-ram-with-firefox
    options.add_argument('--disable-application-cache')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-extensions')

if not DEBUG:
    # Если не тестируем, то Chrome запускаем в "безголовом" режиме.
    options.add_argument('--headless')

options.add_argument('user_agen=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                     'Chrome/97.0.4692.71 Safari/537.36')

if BROWSER == Browser.Firefox:
    driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
else:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Переходим в сервис.
driver.get(EGAIS_ASSORTMENT_URL)
try:
    # Переходим на вкладку входа по паролю.
    time.sleep(TIMEOUT)
    driver.find_element(By.XPATH, '//*[@id="root"]/div/div[1]/div[1]/a[1]').click()

    # Вход в сервис. Регистрация пользователя.
    # Находим input для логина.
    time.sleep(TIMEOUT)
    # В Firefox почему-то добавляется еще один span.
    user_name_element = driver.find_element(By.XPATH,
                                            f'//*[@id="root"]/div/div[1]/span/form/div[1]/div/'
                                            f'{"span/" if BROWSER == Browser.Firefox else ""}span/span/label/span[2]/input')
    user_name_element.clear()
    # Вводим в поле логин.
    user_name_element.send_keys(USER)

    # Находим input для пароля.
    password_element = driver.find_element(By.XPATH,
                                           f'//*[@id="root"]/div/div[1]/span/form/div[2]/div/'
                                           f'{"span/" if BROWSER == Browser.Firefox else ""}span/div/label/span[2]/input')
    password_element.clear()
    # Вводим в поле пароль.
    password_element.send_keys(PASSWORD)

    # Находим кнопки "Войти" и нажимаем ее.
    time.sleep(TIMEOUT)
    driver.find_element(By.XPATH, '/html/body/div[2]/div/div[1]/span/form/div[3]/div[2]/span/button').click()

    # Переход в каталог ЕГАИС номенклатуры
    # Переход в раздел Товары
    # Если не выставить паузу, то следующий driver.get() не сработает
    time.sleep(TIMEOUT + 5)
    driver.get(EGAIS_ASSORTMENT_URL)

    # Словарь для хранения ЕГАИС наименований
    goods_egais: Dict[str, GoodEGAIS] = {}

    # Получаем номер последней страницы с товарами
    time.sleep(TIMEOUT)
    last_page: int = int(driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div/div/div[3]/div/div/div/div[1]/'
                                                       'div/div[2]/div/div/div[2]/div[3]/div/a[6]').text)

    # Проходим циклом по всем страницам, нажимая кнопку >> (перехода на следующую страницу)
    # Т.к. сервис всегда открывает страницу товаров на первой странице, то переходы начанем делать с 2ой
    for page_num in range(1, last_page):

        if not (page_num % 10):
            time.sleep(5 * 60)

        # Перебираем строки таблицы на странице
        for i in range(AMOUNT_GOODS_ON_PAGE):

            # Находим таблицу товаров на странице
            # Если найти таблицу, сохранить список из строк в переменную типа list,
            # потом в цикле проходить по строкам, кликая на них, переходить в отделаьную карточку. То при первом же
            # driver.back(), список строк, который храниться в переменной потеряет связь с driver и на последующий клики
            # будет вылеать exeption.
            # По этой причине каждую итерацию ищем таблицу на странице
            time.sleep(TIMEOUT)
            rows = driver.find_elements(By.XPATH,
                                        '/html/body/div[1]/div/div[2]/div/div/div[3]/div/div/div/div[1]/div/div[2]/div/'
                                        'div/div[2]/div[2]/table/tbody/tr')

            element = rows[i]
            # Переходим в карточку товара
            element.click()
            # Ищем код алкогольной продукции
            alco_code: int = int(driver.find_element(By.CLASS_NAME, '_38Rx4IoiAQIPCFHgLzoC_M').text)
            # Ищем ЕГАИС наменование
            egais_name: str = driver.find_element(By.CLASS_NAME, '_1Jpgo-qz5E8ozjVGHO2u-Y').text
            good = GoodEGAIS(name=egais_name, alco_code=alco_code)
            goods_egais[good.name] = good
            # Переходим на страницу назад, с списком товаров
            driver.back()

        # Нажимаем кнопку >>
        time.sleep(TIMEOUT)
        driver.find_element(By.XPATH,
                            f'/html/body/div[1]/div/div[2]/div/div/div[3]/div/div/div/div[1]/div/div[2]/div/div/div[2]/'
                            f'div[3]/div/a[{str(7) if page_num == 1 else str(8)}]').click()
    driver.quit()
except Exception:
    driver.quit()

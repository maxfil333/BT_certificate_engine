import base64

import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError
from typing import Union

from src.logger import logger
from src.config import config


# ______ HTTP-request ______
def cup_http_request(function, *args, kappa=True) -> Union[list, dict, None]:
    user_1C = config['user_1C']
    password_1C = config['password_1C']

    # Определение серверов
    if kappa:
        primary_base = r'http://kappa5.group.ru:81/ca/hs/interaction/'
        secondary_base = r'http://10.10.0.10:81/ca/hs/interaction/'
    else:
        primary_base = r'http://10.10.0.10:81/ca/hs/interaction/'
        secondary_base = r'http://kappa5.group.ru:81/ca/hs/interaction/'

    function_args = r'/'.join(map(lambda x: base64.urlsafe_b64encode(x.encode()).decode(), args))

    try:
        # Формируем URL для первого сервера
        primary_url = primary_base + function + r'/' + function_args
        logger.print(f"Попытка запроса: {primary_url}")

        # Попытка отправить запрос на первый сервер
        response = requests.get(primary_url, auth=HTTPBasicAuth(user_1C, password_1C))

        # Если первый запрос успешен, возвращаем результат
        if response.status_code == 200:
            return response.json()
        else:
            logger.print(f"Ошибка при запросе к первому серверу: {response.status_code} - {response.reason}")
    except Exception as error:
        logger.print(error)

    try:
        # Формируем URL для второго сервера
        secondary_url = secondary_base + function + r'/' + function_args
        logger.print(f"Попытка запроса ко второму серверу: {secondary_url}")

        # Попытка отправить запрос на второй сервер
        response = requests.get(secondary_url, auth=HTTPBasicAuth(user_1C, password_1C))

        # Возвращаем результат, если успешен
        if response.status_code == 200:
            return response.json()
        else:
            logger.print(f"Ошибка при запросе ко второму серверу: {response.status_code} - {response.reason}")
            return None
    except Exception as error:
        logger.print(error)
        return None


if __name__ == '__main__':

    # ___ some tests ___
    func_name = r'UnitDataByTransactionNumber'
    a1 = r'ТБ-0109677'
    a2 = r'СудноФидер,Грузополучатель'
    print(1, cup_http_request(func_name, a1, a2))  # -> dict

    func_name = r'CustomsTransactionNumberFromBrokerDocument'
    a1 = r'000055211/24'
    print(2, cup_http_request(func_name, a1))  # -> list

    func_name = r'CustomsTransactionNumberFromBrokerDocument'
    a1 = r'000055211/24'
    print(3, cup_http_request(func_name, ''))  # -> None (error 404)

    func_name = r'CustomsTransactionNumberFromBrokerDocument'
    a1 = r'000055211/24'
    print(4, cup_http_request(func_name, 'z'))  # -> []

    func_name = r'CustomsTransactionNumberFromBrokerDocument'
    print(5, cup_http_request(func_name, r'09901230710012475643P'))  # -> list

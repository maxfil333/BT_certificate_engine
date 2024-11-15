import base64
import os.path
import traceback

import requests
from requests.auth import HTTPBasicAuth

from src.config import config
from src.logger import logger

user_1C = config['user_1C']
password_1C = config['password_1C']


def encode_file(file_path: str, url_safe=False) -> str:
    with open(file_path, 'rb') as f:
        res = f.read()
        if url_safe:
            return base64.urlsafe_b64encode(res).decode('utf-8')
        else:
            return base64.b64encode(res).decode('utf-8')


def post_load_afk_conos(dct: dict, original_file: str, new_save_path: str, test=True) -> list:

    result = []

    if dct['Тип документа'] not in ['акт', 'коносамент']:
        return result

    clean_transactions = dct["Номера таможенных сделок без даты"]
    url = "http://10.10.0.10:81/ca/hs/interaction/SendDataToTransaction"

    for transaction in clean_transactions:
        POST_BODY = {}
        
        if dct['Тип документа'] == 'акт':
            POST_BODY["Метод"] = "ФайлВСделку"
            POST_BODY["Параметры"] = {}
            POST_BODY["Параметры"]["НомерСделки"] = transaction
            POST_BODY["Параметры"]["НомерАФК"] = dct['Номер документа']
            POST_BODY["Параметры"]["ТипАФК"] = dct['release']
            POST_BODY["Параметры"]["Данные"] = {}
            POST_BODY["Параметры"]["Данные"]["ИмяФайла"] = os.path.basename(new_save_path)
            POST_BODY["Параметры"]["Данные"]["ДвоичныеДанные"] = encode_file(original_file)

        if dct['Тип документа'] == 'коносамент':
            POST_BODY["Метод"] = "ФайлВСделку"
            POST_BODY["Параметры"] = {}
            POST_BODY["Параметры"]["НомерСделки"] = transaction
            POST_BODY["Параметры"]["НомерКоносамента"] = dct['Номер коносамента']
            POST_BODY["Параметры"]["Данные"] = {}
            POST_BODY["Параметры"]["Данные"]["ИмяФайла"] = os.path.basename(new_save_path)
            POST_BODY["Параметры"]["Данные"]["ДвоичныеДанные"] = encode_file(original_file)

        # Отправка POST-запроса с JSON в теле
        if test:
            POST_BODY["Параметры"]["Данные"]["ДвоичныеДанные"] = 'some bytes data'
            logger.print(POST_BODY)
            result.append(f"POSTED: {transaction}")
        else:
            try:
                response = requests.post(url, json=POST_BODY, auth=HTTPBasicAuth(user_1C, password_1C))
                if response.status_code == 200:
                    result.append(f"POSTED: {transaction}")
                else:
                    message = f"Ошибка при POST-запросе в ЦУП: {response.status_code} - {response.reason}"
                    logger.print(message)
                    result.append(False)
            except:
                logger.print(traceback.format_exc())
                result.append(False)

    return result

import os
import base64
import requests
from requests.auth import HTTPBasicAuth

from src.logger import logger


# ______ HTTP-request ______
def cup_http_request(function, *args, kappa=False):
    user_1C = os.getenv('user_1C')
    password_1C = os.getenv('password_1C')

    if kappa:
        base = r'http://kappa5.group.ru:81/ca/hs/interaction/'
    else:
        base = r'http://10.10.0.10:81/ca/hs/interaction/'

    function_args = r'/'.join(map(lambda x: base64.urlsafe_b64encode(x.encode()).decode(), args))
    url = base + function + r'/' + function_args
    logger.write(url)

    response = requests.get(url, auth=HTTPBasicAuth(user_1C, password_1C))
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Ошибка: {response.status_code} - {response.reason}")

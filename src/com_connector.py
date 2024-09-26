import time
import win32com.client

from src.logger import logger
from src.config import config


def create_connection():
    logger.print('connector initialization...')
    connection_start = time.perf_counter()
    v8com = win32com.client.Dispatch("V83.COMConnector")
    connection = v8com.Connect(config['V83_CONN_STRING'])
    logger.print(f'connection time: {time.perf_counter() - connection_start:.2f}\n')
    return connection

import time
import win32com.client
from logger import logger


def create_connection(connection_params):
    logger.print('connector initialization...')
    connection_start = time.perf_counter()
    v8com = win32com.client.Dispatch("V83.COMConnector")
    connection = v8com.Connect(connection_params)
    logger.print('connection time:', time.perf_counter() - connection_start)
    return connection

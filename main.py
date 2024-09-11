import os
import json
import time
import datetime
import argparse
import traceback
import numpy as np

from glob import glob
from time import perf_counter
from pdf2image import convert_from_path
from openai import PermissionDeniedError

from src.logger import logger
from src.config import config
from src.connector import create_connection
from src.main_edit import image_preprocessor
from src.utils import extract_text_with_fitz, image_split_top_bot, count_pages, folder_former
from src.main_openai import run_chat, certificate_local_postprocessing, appendix_local_postprocessing


def main(connection: None):
    logger.print(f"CONNECTION: <{'true' if connection else 'false'}>")

    # _____ PREPROCESSING FROM IN TO EDITED _____
    image_preprocessor()
    in_folder, edit_folder, out_folder = config['IN'], config['EDITED'], config['OUT']

    folders = sorted([file for file in glob(f"{edit_folder}/*") if os.path.isdir(file)], key=os.path.getctime)
    if not folders:
        return 'EMPTY'

    # _____ GO THROUGH THE EDITED FOLDERS _____
    for folder in folders:
        try:
            logger.print('-' * 50, folder, sep='\n')
            files_ = glob(os.path.join(folder, '*'))
            files = list(filter(lambda x: os.path.splitext(x)[-1].lower() in ['.jpeg', '.jpg', '.png', '.pdf'], files_))

            assert len(files) == 1, f"Количество файлов равно <{len(files)}> в {folder}."

            file, file_type = files[0], os.path.splitext(files[0])[-1]

            with open(os.path.join(folder, 'main_file.json'), 'r', encoding='utf-8') as f:
                dct = json.load(f)
                original_file = dct['path']

            original_file_num_pages = count_pages(original_file)
            if not original_file_num_pages:
                original_file_num_pages = 0

            # __________ RUN CHAT __________
            if file_type.lower() == '.pdf':
                text_mode_content = extract_text_with_fitz(file)
            else:
                text_mode_content = None

            # ___ ищем в основном файле (file) ___
            result = run_chat(file,
                              prompt=config['certificate_system_prompt'],
                              response_format=config['certificate_response_format'],
                              text_mode_content=text_mode_content
                              )
            logger.print('result_cert:', result, sep='\n')
            result = certificate_local_postprocessing(response=result, connection=connection)
            result_dct = json.loads(result)
            logger.print('after local postprocessing:', result)

            # ___ если АКТ, то ищем в приложении ___
            if (connection and result_dct['Тип документа'] == 'акт' and (not result_dct['Номера таможенных сделок'])
                    and original_file_num_pages >= 2):
                # ___ создаем appendix ___
                act_second_page = convert_from_path(original_file, first_page=2, last_page=2, fmt='jpg',
                                                    poppler_path=config["POPPLER_PATH"],
                                                    jpegopt={"quality": 100})
                appendix = act_second_page[0]
                appendix_top, _ = image_split_top_bot(np.array(appendix))
                save_path = os.path.splitext(file)[0] + '_APDX' + '.jpg'
                appendix_top.save(save_path, quality=100)

                # ___ ищем в appendix ___
                result_appendix = run_chat(save_path,
                                           prompt=config['appendix_system_prompt'],
                                           response_format=config['appendix_response_format']
                                           )
                logger.print('result_apdx:', result_appendix, sep='\n')
                result_appendix = appendix_local_postprocessing(response=result_appendix, connection=connection)
                logger.print('after local postprocessing:', result_appendix)

                # ___ добавляем найденное в result ___
                dct, dct_appendix = json.loads(result), json.loads(result_appendix)
                fcc_numbers = dct_appendix['result']['fcc_numbers']
                transaction_numbers = dct_appendix['result']['transaction_numbers']
                dct['Номера фсс'] = fcc_numbers
                dct['Номера таможенных сделок'] = transaction_numbers
                result = json.dumps(dct, ensure_ascii=False, indent=4)
                logger.print('merged result', result)

            # _____  COPY ORIGINAL FILE TO "OUT" _____

            folder_former(json_string=result, original_file=original_file, out_path=config['OUT'])

            # _____  DELETE ORIGINAL FILE FROM "IN" _____

            os.unlink(original_file)
        except PermissionDeniedError:
            raise
        except Exception:
            logger.print('main_error', traceback.format_exc())


def main_loop(sleep_time: int, single_launch: bool, disconnected: bool):
    iteration = 1
    if disconnected:
        connection = None
    else:
        connection = create_connection(config['V83_CONN_STRING'])
    while True:
        print()
        print(f"{'-' * 24} ITERATION - {iteration} {'-' * 24}")
        print()

        start = perf_counter()

        result = None
        try:
            result = main(connection=connection)
        except PermissionDeniedError:
            logger.print('ОШИБКА ВЫПОЛНЕНИЯ:\n!!! Включите VPN !!!')

        if result == 'EMPTY':
            logger.clear()
        else:
            os.makedirs(os.path.join(config['OUT'], '__logs__'), exist_ok=True)
            logger.save(os.path.join(config['OUT'], '__logs__'))
            logger.clear()

        print(f"{time.perf_counter() - start:.2f}")

        print()
        print(f"{'-' * 20} ITERATION - {iteration} COMPLETED {'-' * 20}")
        print()

        if single_launch:
            break

        print('next iteration: ', end='')
        print((datetime.datetime.now() + datetime.timedelta(seconds=sleep_time)).strftime('%d.%m.%Y %H:%M:%S'))
        time.sleep(sleep_time)
        iteration += 1


if __name__ == '__main__':
    DEFAULT_SLEEP_TIME = 20

    parser = argparse.ArgumentParser()
    parser.add_argument('-st', '--sleep_time', type=int, help='time between launches')
    parser.add_argument('-sl', '--single_launch', action='store_true', help='run only once')
    parser.add_argument('-d', '--disconnected', action='store_true', help='run without 1C connector')
    args = parser.parse_args()

    main_loop(
        sleep_time=args.sleep_time if args.sleep_time is not None else DEFAULT_SLEEP_TIME,
        single_launch=args.single_launch,
        disconnected=args.disconnected
    )

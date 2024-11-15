import os
import json
import time
import datetime
import argparse
import traceback
import numpy as np
from typing import Union, Literal
from win32com.client import CDispatch

from glob import glob
from time import perf_counter
from pdf2image import convert_from_path
from openai import PermissionDeniedError

from src.logger import logger
from src.config import config
from src.com_connector import create_connection
from src.main_edit import image_preprocessor
from src.main_openai import run_chat
from src.response_postprocessing import main_postprocessing, appendix_postprocessing
from src.response_postprocessing import get_consignee_and_feeder, get_clean_transactions
from src.release_postprocessing import add_release_permitted
from src.utils import extract_text_with_fitz, image_split_top_bot, count_pages, folder_former


def main(connection: Union[None, Literal['http'], CDispatch]):

    # __________ CONNECTION __________
    logger.print(f"CONNECTION: <{connection}>")

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
            result = main_postprocessing(response=result, connection=connection)

            # ___ если АКТ, то ищем в приложении ___
            res_dct = json.loads(result)
            if (connection and res_dct['Тип документа'] == 'акт' and (not res_dct['Номера таможенных сделок'])
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
                result_appendix = appendix_postprocessing(response=result_appendix, connection=connection)
                logger.print('appendix_local_postprocessing result:', result_appendix)

                # ___ добавляем найденное в result ___
                main_dict, appendix_dict = json.loads(result), json.loads(result_appendix)
                main_dict['Номера таможенных сделок'] = appendix_dict['Номера таможенных сделок']
                main_dict['Номера фсс'] = appendix_dict['Номера фсс']
                result = json.dumps(main_dict, ensure_ascii=False, indent=4)

            # _____  GET CLEAN TRANSACTIONS _____
            result = get_clean_transactions(result)

            # _____  GET CONSIGNEE AND FEEDER _____
            result = get_consignee_and_feeder(result, connection)

            # _____  ADD RELEASE TO RESULT _____
            result = add_release_permitted(current_folder=folder, result=result)

            # _____  COPY ORIGINAL FILE TO "OUT" _____
            folder_former(json_string=result, original_file=original_file, out_path=out_folder)

            # _____  DELETE ORIGINAL FILE FROM "IN" _____
            os.unlink(original_file)

            # _____  PRINT RESULT JSON  _____
            logger.print("RESULT JSON:")
            logger.print(result)

        except PermissionDeniedError:
            raise
        except Exception:
            logger.print('main_error', traceback.format_exc())


def main_loop(sleep_time: int, single_launch: bool, use_com_connector: bool, ignore_connection: bool):

    # _______ CONNECTION ________
    if ignore_connection is False:
        if use_com_connector:
            connection = create_connection()
        else:
            connection = 'http'
    else:
        connection = None

    iteration = 1
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

        print(f"ITERATION TIME: {perf_counter() - start:.2f}")

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
    parser.add_argument('-ucc', '--use_com_connector', action='store_true', help='use com connector')
    parser.add_argument('-ic', '--ignore_connection', action='store_true', help='run without 1C connection')
    args = parser.parse_args()

    main_loop(
        sleep_time=args.sleep_time if args.sleep_time is not None else DEFAULT_SLEEP_TIME,
        single_launch=args.single_launch,
        use_com_connector=args.use_com_connector,
        ignore_connection=args.ignore_connection
    )

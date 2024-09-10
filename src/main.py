import os
import json
from glob import glob

import numpy as np
import win32com.client
from time import perf_counter
from pdf2image import convert_from_path
from openai import PermissionDeniedError

from config import config
from main_edit import image_preprocessor
from main_openai import run_chat, certificate_local_postprocessing, appendix_local_postprocessing
from utils import extract_text_with_fitz, image_split_top_bot, count_pages, folder_former, extract_pages


def main(connection: bool):
    print(f"CONNECTION: <{connection}>")

    # _____ CONNECT 1C _____
    if connection:
        v8com = win32com.client.Dispatch("V83.COMConnector")
        connection = v8com.Connect(config['V83_CONN_STRING'])

    # _____ PREPROCESSING FROM IN TO EDITED _____
    image_preprocessor()
    in_folder, edit_folder, out_folder = config['IN'], config['EDITED'], config['OUT']

    folders = sorted([file for file in glob(f"{edit_folder}/*") if os.path.isdir(file)], key=os.path.getctime)

    # _____ GO THROUGH THE EDITED FOLDERS _____
    for folder in folders:
        print('-' * 50, folder, sep='\n')
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
        # TODO: check assistant vs chat
        if file_type.lower() == '.pdf':
            text_mode_content = extract_text_with_fitz(
                extract_pages(file, pages_to_keep=[1, 2, 3])  # max_pages to model = 3
            )
        else:
            text_mode_content = None

        # ___ ищем в основном файле (file) ___
        result = run_chat(file,
                          prompt=config['certificate_system_prompt'],
                          response_format=config['certificate_response_format'],
                          text_mode_content=text_mode_content
                          )
        print('result_cert:', result, sep='\n')
        result = certificate_local_postprocessing(response=result, connection=connection)
        result_dct = json.loads(result)
        print('after local postprocessing:', result)

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
            print('result_apdx:', result_appendix, sep='\n')
            result_appendix = appendix_local_postprocessing(response=result_appendix, connection=connection)
            print('after local postprocessing:', result_appendix)

            # ___ добавляем найденное в result ___
            dct, dct_appendix = json.loads(result), json.loads(result_appendix)
            fcc_numbers = dct_appendix['result']['fcc_numbers']
            transaction_numbers = dct_appendix['result']['transaction_numbers']
            dct['Номера фсс'] = fcc_numbers
            dct['Номера таможенных сделок'] = transaction_numbers
            result = json.dumps(dct, ensure_ascii=False, indent=4)
            print('merged result', result)

        # _____  COPY ORIGINAL FILE TO "OUT" _____

        folder_former(json_string=result, original_file=original_file, out_path=config['OUT'])

        # _____  DELETE ORIGINAL FILE FROM "IN" _____

        os.unlink(original_file)


if __name__ == '__main__':
    start = perf_counter()
    try:
        main(connection=True)
    except PermissionDeniedError:
        print('ОШИБКА ВЫПОЛНЕНИЯ:\n!!! Включите VPN !!!')
    print(f'time: {perf_counter() - start:.2f}')

import os
import json
import shutil
from glob import glob
import win32com.client
from time import perf_counter

from config import config
from main_openai import run_chat, certificate_local_postprocessing, appendix_local_postprocessing
from main_edit import image_preprocessor, folder_former


# TODO: обработчик pdf

def main(connection: bool):
    # _____ CONNECT 1C _____
    if connection:
        v8com = win32com.client.Dispatch("V83.COMConnector")
        connection = v8com.Connect(config['V83_CONN_STRING'])

    # _____ PREPROCESSING FROM IN TO EDITED _____
    image_preprocessor()
    in_folder, edit_folder, out_folder = config['IN'], config['EDITED'], config['OUT']

    folders = sorted([file for file in glob(f"{edit_folder}/*") if os.path.isdir(file)], key=os.path.getctime)

    # _____ GO THROUGH THE FOLDERS _____
    for folder in folders:
        print('-' * 50)
        print(folder)
        certificate, appendix = None, None
        files = glob(os.path.join(folder, '*'))
        files = list(filter(lambda x: os.path.splitext(x)[-1] in ['.jpeg', '.jpg', '.png', '.pdf'], files))
        if len(files) == 1:
            certificate = files[0]
        elif len(files) == 2:
            files_ = files.copy()
            appendix = list(filter(lambda x: os.path.splitext(x)[0][-5:] == '_APDX', files))[0]
            files_.pop(files_.index(appendix))
            certificate = files_[0]
        else:
            print(f'Количество файлов в папке {folder} более 3-х')
            continue

        # __________ RUN CHAT __________

        # ___ ищем в сертификате ___
        result = run_chat(certificate,
                          prompt=config['certificate_system_prompt'],
                          response_format=config['certificate_response_format']
                          )
        print('result_cert:', result, sep='\n')
        result = certificate_local_postprocessing(response=result, connection=connection)
        print('after local postprocessing:', result)

        # ___ ищем в приложении ___
        if connection and appendix and (not json.loads(result)['Номера таможенных сделок']):
            result_appendix = run_chat(appendix,
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

        with open(os.path.join(folder, 'main_file.txt'), 'r', encoding='utf-8') as f:
            original_file = f.read().strip()

        folder_former(json_string=result, original_file=original_file, out_path=config['OUT'])

        # _____  DELETE ORIGINAL FILE FROM "IN" _____

        os.unlink(original_file)


if __name__ == '__main__':
    start = perf_counter()
    main(connection=True)
    print(f'time: {perf_counter() - start:.2f}')

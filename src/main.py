import os
import shutil
from glob import glob
import win32com.client
from time import perf_counter

from config import config
from main_openai import run_chat
from main_edit import image_preprocessor


# TODO: обработчик pdf
# TODO: shutil.copy оригинальный файл а не обрезанный
# TODO: формирование папки

def main(connection: bool):

    # _____ CONNECT 1C _____
    if connection:
        v8com = win32com.client.Dispatch("V83.COMConnector")
        connection = v8com.Connect(config['V83_CONN_STRING'])

    # _____ PREPROCESSING FROM IN TO EDITED _____
    image_preprocessor()
    in_folder, edit_folder, check_folder = config['IN'], config['EDITED'], config['CHECK']
    images = [file for file in glob(f"{edit_folder}/*.*")
              if os.path.splitext(file)[-1] in ['.jpeg', '.jpg', '.png']]
    sorted_images = sorted(images, key=os.path.getctime)

    # _____ RUN CHAT _____
    for img in sorted_images:
        try:
            result = run_chat(img, connection=connection)
            print('result:', result, sep='\n')

            original_image = os.path.join(in_folder, os.path.basename(img))
            edited_image = os.path.join(edit_folder, os.path.basename(img))

            shutil.copy(os.path.join(check_folder, original_image), check_folder)

            os.unlink(original_image)
            os.unlink(edited_image)
            json_path = os.path.join(check_folder, os.path.splitext(os.path.basename(img))[0] + '.json')
            with open(json_path, 'w', encoding='utf-8') as file:
                file.write(result)

        except Exception as error:
            print(error)


if __name__ == '__main__':
    start = perf_counter()
    main(connection=True)
    print(f'time: {perf_counter()-start:.2f}')

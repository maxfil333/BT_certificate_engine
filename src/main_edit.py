import os
import json
import shutil

import numpy as np
from glob import glob
from pdf2image import convert_from_path

from config import config
from utils import delete_all_files, image_split_top_bot, get_unique_filename, is_scanned_pdf, count_pages


def image_preprocessor() -> None:
    """ preprocess and copy images from IN to EDITED """

    print('main_edit.image_preprocessor...')
    in_folder, edit_folder = config['IN'], config['EDITED']

    # ___ clear edited folder ___
    print('clearing EDITED...')
    delete_all_files(edit_folder)

    # ___ collect files in IN-folder ___
    files = [file for file in glob(f"{in_folder}/*.*")
             if os.path.splitext(file)[-1].lower() in ['.jpeg', '.jpg', '.png', '.pdf']]

    # ___ create folder in EDITED-folder for each file ___
    for file in sorted(files, key=os.path.getctime):
        print(file)
        base, ext = os.path.splitext(file)
        clear_name = os.path.splitext(os.path.split(file)[-1])[0]
        folder_path = f'{os.path.join(edit_folder, clear_name)}({ext.replace(".", "")})'
        os.makedirs(folder_path, exist_ok=False)
        save_path = os.path.join(folder_path, os.path.basename(file))
        with open(os.path.join(folder_path, 'main_file.txt'), 'w', encoding='utf-8') as f:
            f.write(file)

        # _____ pdf _____
        if ext == '.pdf':
            num_pages = count_pages(file)
            scanned = is_scanned_pdf(file)

            # ___ pdf scanned ___
            if scanned:
                images = convert_from_path(file, first_page=1, last_page=1, fmt='jpg',
                                           poppler_path=config["POPPLER_PATH"],
                                           jpegopt={"quality": 100})

                # take the first page to classify it using GPT
                first_page = np.array(images[0])
                first_page_top, _ = image_split_top_bot(first_page)
                save_path = os.path.splitext(save_path)[0] + '.jpg'
                first_page_top.save(save_path, quality=100)

            # ___ pdf digital ___
            else:
                shutil.copy(file, save_path)

        # _____ images _____
        else:
            top, _ = image_split_top_bot(file)
            top.save(save_path, quality=100)


def folder_former(json_string: str, original_file: str, out_path: str) -> None:
    dct = json.loads(json_string)
    doc_type = dct['Тип документа']
    doc_number = dct['Номер документа']
    doc_conos = dct['Номер коносамента']
    transactions = dct['Номера таможенных сделок']
    if doc_type == 'act':
        if not doc_number:
            doc_number = 'untitled_number'
        new_name = doc_number + os.path.splitext(original_file)[-1]
    else:
        if not doc_conos:
            doc_conos = 'untitled_conos'
        new_name = doc_conos + os.path.splitext(original_file)[-1]

    if not transactions:
        target_dir: str = config['untitled']
        new_path = get_unique_filename(os.path.join(target_dir, new_name))
        shutil.copy(original_file, new_path)
    else:
        for transaction in transactions:
            target_dir = os.path.join(out_path, transaction)
            if not os.path.isdir(target_dir):
                os.makedirs(target_dir, exist_ok=False)
            new_path = get_unique_filename(os.path.join(target_dir, new_name))
            shutil.copy(original_file, new_path)


if __name__ == '__main__':
    image_preprocessor()

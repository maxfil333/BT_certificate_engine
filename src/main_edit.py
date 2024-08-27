import os
import json
import shutil

import numpy as np
from glob import glob
from pdf2image import convert_from_path

from config import config
from utils import delete_all_files, image_split_top_bot, get_unique_filename


def image_preprocessor() -> None:
    """ preprocess and copy images from IN to EDITED """

    # ___ clear edited folder ___

    in_folder, edit_folder = config['IN'], config['EDITED']
    delete_all_files(edit_folder)

    # ___ create new folders ___

    files = [file for file in glob(f"{in_folder}/*.*")
             if os.path.splitext(file)[-1] in ['.jpeg', '.jpg', '.png', '.pdf']]

    for file in sorted(files, key=os.path.getctime):
        base, ext = os.path.splitext(file)
        clear_name = os.path.splitext(os.path.split(file)[-1])[0]
        folder_path = f'{os.path.join(edit_folder, clear_name)}({ext.replace(".", "")})'
        os.makedirs(folder_path, exist_ok=False)
        save_path = os.path.join(folder_path, os.path.basename(file))
        with open(os.path.join(folder_path, 'main_file.txt'), 'w', encoding='utf-8') as f:
            f.write(file)

        # _____ pdf _____
        if ext == '.pdf':
            images = convert_from_path(file, first_page=1, last_page=2, fmt='jpg',
                                       poppler_path=config["POPPLER_PATH"],
                                       jpegopt={"quality": 100})

            if len(images) >= 2:
                certificate, appendix = np.array(images[0]), np.array(images[1])
            else:
                certificate, appendix = np.array(images[0]), None

            cer_top, cer_bot = image_split_top_bot(certificate)
            save_path = os.path.splitext(save_path)[0] + '.jpg'
            cer_top.save(save_path, quality=100)

            if appendix is not None:
                apdx_top, apdx_bot = image_split_top_bot(appendix)
                save_path = os.path.splitext(save_path)[0] + '_APDX' + '.jpg'
                apdx_top.save(save_path, quality=100)

        # _____ images _____
        else:
            top, bot = image_split_top_bot(file)
            top.save(save_path, quality=100)


def folder_former(json_string: str, original_file: str, out_path: str) -> None:
    dct = json.loads(json_string)
    doc_number = dct['Номер документа']
    transactions = dct['Номера таможенных сделок']
    new_name = doc_number + os.path.splitext(original_file)[-1]

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

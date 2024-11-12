import os
import json

import numpy as np
from glob import glob
from pdf2image import convert_from_path

from src.logger import logger
from src.config import config
from src.document_classifier import text_classifier
from src.utils import delete_all_files, image_split_top_bot, magick_convert
from src.utils import extract_text_with_fitz, is_scanned_pdf, extract_pages, clear_waste_pages


def image_preprocessor() -> None:
    """ preprocess and copy images from IN to EDITED """

    logger.print('main_edit.image_preprocessor...')
    in_folder, edit_folder = config['IN'], config['EDITED']

    # ___ clear edited folder ___
    logger.print('clearing EDITED...')
    delete_all_files(edit_folder)

    # ___ collect files in IN-folder ___
    files = [file for file in glob(f"{in_folder}/*.*")
             if os.path.splitext(file)[-1].lower() in ['.jpeg', '.jpg', '.png', '.pdf']]

    # ___ create folder in EDITED-folder for each file ___
    for file in sorted(files, key=os.path.getctime):
        logger.print(file)
        base, ext = os.path.splitext(file)
        clear_name = os.path.splitext(os.path.split(file)[-1])[0]
        folder_path = f'{os.path.join(edit_folder, clear_name)}({ext.replace(".", "")})'
        os.makedirs(folder_path, exist_ok=False)
        save_path = os.path.join(folder_path, os.path.basename(file))

        file_params: list = list()
        # _____ pdf _____
        if ext.lower() == '.pdf':
            scanned = is_scanned_pdf(file)

            # ___ pdf scanned ___
            if scanned:
                file_params.append('scanned')
                images = convert_from_path(file, first_page=1, last_page=1, fmt='jpg',
                                           poppler_path=config["POPPLER_PATH"],
                                           jpegopt={"quality": 100})

                # take the first page (top half) to classify it using GPT
                first_page = np.array(images[0])
                first_page_top, _ = image_split_top_bot(first_page, top_y_shift=0)
                save_path = os.path.splitext(save_path)[0] + '.jpg'
                first_page_top.save(save_path, quality=100)
                magick_convert(save_path)

            # ___ pdf digital ___
            else:
                file_params.append('digital')
                first_page_text = extract_text_with_fitz(file, pages=[1])
                pdf_class = text_classifier(first_page_text)
                if pdf_class == 'conos':
                    extract_pages(file, pages_to_keep=[1], output_pdf_path=save_path)
                else:
                    cleared = clear_waste_pages(file)
                    extract_pages(cleared, pages_to_keep=[1, 2, 3], output_pdf_path=save_path)  # max_pages to model = 3
                file_params.append(pdf_class if pdf_class else 'no_text_class')

        # _____ images _____
        else:
            file_params.append('image')
            top, _ = image_split_top_bot(file)
            top.save(save_path, quality=100)

        with open(os.path.join(folder_path, 'main_file.json'), 'w', encoding='utf-8') as f:
            dct = {"path": file, "params": '|'.join(file_params)}
            json.dump(dct, f, indent=4)


if __name__ == '__main__':
    image_preprocessor()

import os
import re
import random
import shutil
import numpy as np
from PIL import Image
from glob import glob
from tqdm import tqdm
from pdf2image import convert_from_path

from src.config import config


class BreakException(Exception):
    pass


def parse(pdf_path, n_folders, shift_folders, max_pdf_amount, save_folder=None):
    folders = glob(os.path.join(pdf_path, r'*'))
    folders.sort(key=os.path.getmtime, reverse=True)
    folders = [f for f in folders if os.path.isdir(f)]
    folders = folders[0 + shift_folders: n_folders + shift_folders]  # <-- новые : старые -->
    result = []
    try:
        for f in tqdm(folders):
            pdfs = glob(os.path.join(os.path.abspath(f), '**', '*.pdf'), recursive=True)
            for pdf in pdfs:
                if re.findall(r'.*PATTERN.*', pdf, re.IGNORECASE):
                    print(f, pdf)
                result.append(pdf)
                if len(result) == max_pdf_amount:
                    raise BreakException
    except BreakException:
        pass

    if save_folder:
        for i, r in enumerate(result):
            print(i, r)
            shutil.copy(r, save_folder)

    return result


def save_random_sample(pdf_path, save_folder, k):
    files = glob(os.path.join(pdf_path, r'*.pdf'))
    try:
        files = random.sample(files, k=k)
    except ValueError:
        k = 1
        files = random.sample(files, k=k)

    for i, f in enumerate(tqdm(files)):
        new = shutil.copy(f, save_folder)
        os.rename(new, (os.path.join(os.path.dirname(new), f'{i+1}.pdf')))


if __name__ == '__main__':

    pdf_path = r'C:\Users\Filipp\PycharmProjects\BT_certificate_engine\data'
    save_path = r'C:\Users\Filipp\PycharmProjects\BT_certificate_engine\data_random_4'

    save_random_sample(pdf_path, save_path, k=50)

    # for file in glob(os.path.join(save_path, r'*.pdf')):
    #     image = np.array(convert_from_path(file, first_page=0, last_page=1, fmt='jpg',
    #                                        poppler_path=config["POPPLER_PATH"],
    #                                        jpegopt={"quality": 100})[0])
    #     jpg_path = os.path.splitext(file)[0] + '.jpg'
    #     Image.fromarray(image).save(jpg_path, quality=100)

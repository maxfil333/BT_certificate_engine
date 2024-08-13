import os
import numpy as np
from PIL import Image
from glob import glob

from config import config
from utils import image_split_top_bot
from rotator import main as rotate


def image_preprocessor():
    """ preprocess and copy images from IN to EDITED"""

    in_folder, edit_folder = config['IN'], config['EDITED']

    # TODO: добавить обработчик --- '.pdf',  ---
    images = [file for file in glob(f"{in_folder}/*.*")
              if os.path.splitext(file)[-1] in ['.jpeg', '.jpg', '.png']]
    sorted_images = sorted(images, key=os.path.getctime)

    for img in sorted_images:
        top, bot = image_split_top_bot(img)
        name = os.path.basename(os.path.splitext(img)[0])
        top.save(os.path.join(config['EDITED'], f'{name}.jpg'), quality=100)


def folder_former():
    pass


if __name__ == '__main__':
    image_preprocessor()

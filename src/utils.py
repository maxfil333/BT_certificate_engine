import os
import io
import sys
import json
import fitz
import base64
import msvcrt
from glob import glob

import numpy as np
from PIL import Image
from io import BytesIO, StringIO
from pdf2image import convert_from_path
from rotator import main as rotate


from logger import logger


# _____ PDF _____

def extract_text_with_fitz(pdf_path):
    document = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(document)):
        page = document.load_page(page_num)  # загружаем страницу
        text += page.get_text()  # извлекаем текст
    return text


# _________ ENCODERS _________

# Function to encode the image
def base64_encode_image(image_path: str):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def base64_encode_pil(image: Image.Image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')


# _________ IMAGES _________

def image_split_top_bot(img_path: str) -> list[Image.Image]:
    # 1, 3 -> x; 2, 4 -> y
    pil_image = Image.open(img_path)
    top = pil_image.crop((0, pil_image.height * 0.1, pil_image.width, pil_image.height // 2))
    bot = pil_image.crop((0, pil_image.height // 2, pil_image.width, pil_image.height))
    return top, bot


if __name__ == '__main__':
    # pth = r'C:\Users\Filipp\PycharmProjects\BT_certificate_engine\data_random_6\16.jpg'
    # top, bot = image_split_top_bot(pth)
    # top, bot = Image.fromarray(rotate(np.array(top))), Image.fromarray(rotate(np.array(bot)))
    #
    # top.save(os.path.join(os.path.dirname(pth), '16top.jpg'))
    # bot.save(os.path.join(os.path.dirname(pth), '16bot.jpg'))

    save_path = r'C:\Users\Filipp\PycharmProjects\BT_certificate_engine\data_random_6'
    for img in glob(r'C:\Users\Filipp\PycharmProjects\BT_certificate_engine\data_random\*.jpg'):
        print(img)
        top, bot = image_split_top_bot(img)
        top = Image.fromarray(rotate(np.array(top)))
        bot = Image.fromarray(rotate(np.array(bot)))
        name = os.path.basename(os.path.splitext(img)[0])
        top.save(os.path.join(save_path, f'{name}.jpg'))



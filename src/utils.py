import os
import fitz
import base64
import shutil
import numpy as np
from PIL import Image
from io import BytesIO


# _____ FOLDERS _____

def delete_all_files(dir_path: str):
    for folder_ in os.scandir(dir_path):
        if folder_.is_dir():
            shutil.rmtree(folder_.path)
        else:
            os.remove(folder_.path)


# _____ COMMON _____

def get_unique_filename(filepath):
    if not os.path.exists(filepath):
        return filepath
    else:
        base, ext = os.path.splitext(filepath)
        counter = 1
        while os.path.exists(f"{base}({counter}){ext}"):
            counter += 1
        return f"{base}({counter}){ext}"


def switch_to_latin(s: str, reverse: bool = False) -> str:
    cyrillic_to_latin = {'А': 'A', 'В': 'B', 'Е': 'E', 'К': 'K', 'М': 'M', 'Н': 'H', 'О': 'O', 'Р': 'P', 'С': 'C',
                         'Т': 'T', 'У': 'Y', 'Х': 'X'}
    latin_to_cyrillic = {'A': 'А', 'B': 'В', 'E': 'Е', 'K': 'К', 'M': 'М', 'H': 'Н', 'O': 'О', 'P': 'Р', 'C': 'С',
                         'T': 'Т', 'Y': 'У', 'X': 'Х'}
    new = ''
    if not reverse:
        for letter in s:
            if letter in cyrillic_to_latin:
                new += cyrillic_to_latin[letter]
            else:
                new += letter
    else:
        for letter in s:
            if letter in latin_to_cyrillic:
                new += latin_to_cyrillic[letter]
            else:
                new += letter
    return new


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

def image_split_top_bot(image: str | np.ndarray) -> tuple[Image.Image, Image.Image]:
    # 1, 3 -> x; 2, 4 -> y
    if isinstance(image, np.ndarray):
        pil_image = Image.fromarray(image)
    else:
        pil_image = Image.open(image)
    top = pil_image.crop((0, pil_image.height * 0.1, pil_image.width, pil_image.height // 2))
    bot = pil_image.crop((0, pil_image.height // 2, pil_image.width, pil_image.height))
    return top, bot


if __name__ == '__main__':
    pass

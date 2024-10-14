import os
import re
import fitz
import json
import base64
import shutil
import PyPDF2
import asyncio
import traceback
import numpy as np
from PIL import Image
from io import BytesIO
from aiogram import Bot
from typing import Optional


from src.logger import logger
from src.config import config


# _____ FOLDERS _____

def delete_all_files(dir_path: str):
    for folder_ in os.scandir(dir_path):
        if folder_.is_dir():
            shutil.rmtree(folder_.path)
        else:
            os.remove(folder_.path)


def bot_send_message_to_channel(bot: Bot, message: str, channel_id: str):
    async def send_message_to_channel(channel_id: int | str, message: str):
        await bot.send_message(chat_id=channel_id, text=message)
        await bot.session.close()
    try:
        asyncio.run(send_message_to_channel(channel_id, message))
    except Exception:
        logger.print(traceback.format_exc())


def folder_former(json_string: str, original_file: str, out_path: str) -> None:
    # ___ generate document name ___
    dct = json.loads(json_string)
    doc_type = dct['Тип документа']
    show_doc_type = {'акт': 'Акт', 'коносамент': 'КС', 'заключение': 'Закл.', 'протокол': 'Протокол'}
    transliteration = {'акт': 'act', 'коносамент': 'conos', 'заключение': 'report', 'протокол': 'protocol'}
    doc_number = dct['Номер документа']
    doc_conos = dct['Номер коносамента']
    transactions = dct['Номера таможенных сделок']
    cdf = dct['consignee_deal_feeder']
    cdf_short = dct['consignee_deal_feeder_short']

    if doc_type == 'коносамент':
        if not doc_conos:
            doc_conos = 'untitled_conos'
        new_name = sanitize_filename(doc_conos + os.path.splitext(original_file)[-1])
    else:
        if not doc_number:
            doc_number = f'untitled_{transliteration[doc_type]}'
        new_name = sanitize_filename(doc_number + os.path.splitext(original_file)[-1])

    # ___ distribute into folders ___
    if not transactions:
        os.makedirs(config['untitled'], exist_ok=True)
        target_dir: str = config['untitled']
        new_path = get_unique_filename(os.path.join(target_dir, new_name))
        shutil.copy(original_file, new_path)
        bot_send_message_to_channel(bot=config['bot'], channel_id=config['channel_id'], message=f'untitled: {new_name}')
    else:
        for i, cdf_ in enumerate(cdf_short):
            target_dir = os.path.join(out_path, sanitize_filename(cdf_))
            if not os.path.isdir(target_dir):
                os.makedirs(target_dir, exist_ok=False)
            new_path = get_unique_filename(os.path.join(target_dir, new_name))
            shutil.copy(original_file, new_path)
            bot_send_message_to_channel(bot=config['bot'], channel_id=config['channel_id'],
                                        message=f"{show_doc_type[doc_type]}: {cdf[i]}")


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


def sanitize_filename(filename: str) -> str:
    # Заменяем все недопустимые символы на пробелы
    sanitized = re.sub(r'[\<\>\/\"\\\|\?\*]', ' ', filename)

    # Убираем повторяющиеся пробелы
    sanitized = re.sub(r'\s+', ' ', sanitized)

    # Убираем пробелы в начале и конце строки
    sanitized = sanitized.strip()

    return sanitized


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

def count_pages(file_path: str) -> int | None:
    try:
        # Открытие PDF файла
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            return len(reader.pages)

    except Exception:
        return None


def extract_text_with_fitz(pdf_data: str | bytes, pages: list[int] = None) -> str:
    # Проверяем, что за тип данных передан в pdf_data
    if isinstance(pdf_data, bytes):
        document = fitz.open("pdf", pdf_data)  # открываем PDF из bytes
    else:
        document = fitz.open(pdf_data)  # открываем PDF по пути
    text = ""
    # Если pages не указаны, извлекаем текст со всех страниц
    if pages is None:
        valid_pages_to_extract = list(range(1, document.page_count + 1))
    else:
        valid_pages = [x + 1 for x in range(document.page_count)]
        valid_pages_to_extract = [x for x in pages if x in valid_pages]

    for page_num in valid_pages_to_extract:
        page = document.load_page(page_num - 1)  # загружаем страницу по номеру
        text += page.get_text()  # извлекаем текст

    if isinstance(pdf_data, str):
        document.close()

    return text


def clear_waste_pages(pdf_path: str) -> bytes:
    """Удаляет лишние страницы и возвращает PDF в виде байтов."""

    reader = PyPDF2.PdfReader(pdf_path)
    writer = PyPDF2.PdfWriter()
    num_pages = len(reader.pages)

    # Проверка текста на каждой странице
    for page_num in range(num_pages):
        page = reader.pages[page_num]
        text = page.extract_text()

        if len(text.strip()) > 8000:  # страница сплошного текста
            pass
        elif len(text.strip()) < 75:  # пустая страница или сканированная (нераспознаваемая)
            pass
        else:
            writer.add_page(page)

    # Записываем PDF в память
    pdf_bytes = BytesIO()
    writer.write(pdf_bytes)

    # Возвращаем байты
    return pdf_bytes.getvalue()


def extract_pages(input_pdf: str | bytes,
                  pages_to_keep: list[int],
                  output_pdf_path: Optional[str] = None) -> Optional[bytes]:
    """Извлечение страниц из PDF. Если output_pdf_path не задан, возвращает байты."""

    # Проверяем, что было передано: путь к файлу или байты
    if isinstance(input_pdf, bytes):
        input_pdf_file = BytesIO(input_pdf)
    else:
        input_pdf_file = open(input_pdf, "rb")

    try:
        reader = PyPDF2.PdfReader(input_pdf_file)
        writer = PyPDF2.PdfWriter()
        valid_pages = [x + 1 for x in range(len(reader.pages))]
        valid_pages_to_keep = [x for x in pages_to_keep if x in valid_pages]

        # Извлекаем указанные страницы
        for page_num in valid_pages_to_keep:
            # Нумерация страниц в PyPDF2 начинается с 0
            writer.add_page(reader.pages[page_num - 1])

        if output_pdf_path:
            # Записываем результат в новый PDF файл
            with open(output_pdf_path, "wb") as output_pdf_file:
                writer.write(output_pdf_file)
        else:
            # Создаем байтовый буфер для хранения результата
            output_buffer = BytesIO()
            writer.write(output_buffer)

            # Возвращаем байты PDF-файла
            return output_buffer.getvalue()

    finally:
        # Закрываем файл, если он был открыт
        if not isinstance(input_pdf, bytes):
            input_pdf_file.close()


def is_scanned_pdf(file_path, pages_to_analyse=None):
    try:
        # Открытие PDF файла
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            num_pages = len(reader.pages)
            if pages_to_analyse:
                pages = list(map(lambda x: x - 1, pages_to_analyse))
            else:
                pages = list(range(num_pages))

            # Проверка текста на каждой странице
            scan_list, digit_list = [], []
            for page_num in pages:
                page = reader.pages[page_num]
                text = page.extract_text()
                if len(text.strip()) > 100:
                    digit_list.append(page_num)  # Если текст найден (в достаточном количестве)
                else:
                    scan_list.append(page_num)  # Если текст не найден

            if not scan_list:
                return False
            elif not digit_list:
                return True
            else:
                logger.print(f'! utils.is_scanned_pdf: mixed pages types in {file_path} !')
                return 0 in scan_list  # определяем по первой странице

    except Exception as e:
        logger.print(f"Error reading PDF file: {e}")
        return None


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

def image_split_top_bot(image: str | np.ndarray, top_y_shift=0) -> tuple[Image.Image, Image.Image]:
    if not 0 <= top_y_shift <= 1:
        raise ValueError('Значение должно быть в диапазоне от 0 до 1')

    # 1, 3 -> x; 2, 4 -> y
    if isinstance(image, np.ndarray):
        pil_image = Image.fromarray(image)
    else:
        pil_image = Image.open(image)
    top = pil_image.crop((0, pil_image.height * top_y_shift,
                          pil_image.width, pil_image.height // 2))
    bot = pil_image.crop((0, pil_image.height // 2,
                          pil_image.width, pil_image.height))
    return top, bot


# _________ SERVICES _________

def try_exec(function, *args, return_when_fails=''):
    try:
        return function(*args)
    except Exception:
        logger.print(traceback.format_exc())
        return return_when_fails


if __name__ == '__main__':
    pass

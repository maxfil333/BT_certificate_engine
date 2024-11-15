import os
import json

from src.main_openai import run_chat
from src.utils import release_crop_and_save

release_prompt = """
Ты ассистент. 
Проанализируй предписываемые карантинные фитосанитарные мероприятия.
Ответь "БЕЗ ПРАВА РЕАЛИЗАЦИИ" или "С ПРАВОМ РЕАЛИЗАЦИИ"

Пример 1:
TEXT:
Выпуск разрешен без права реализации.
ASSISTANT:
"БЕЗ ПРАВА РЕАЛИЗАЦИИ"

Пример 2:
TEXT:
Выпуск разрешен. Заключение экспертизы №.
ASSISTANT:
"С ПРАВОМ РЕАЛИЗАЦИИ"

Пример 3:
TEXT:
Выпуск разрешен.
ASSISTANT:
"С ПРАВОМ РЕАЛИЗАЦИИ"
""".strip()

release_schema = {
    "name": "document",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "release": {
                "type": "string",
                "enum": ["С ПРАВОМ РЕАЛИЗАЦИИ", "БЕЗ ПРАВА РЕАЛИЗАЦИИ"]
            }
        },
        "required": ["release"],
        "additionalProperties": False
    }
}

release_response_format = {"type": "json_schema", "json_schema": release_schema}


def add_release_permitted(current_folder: str, result: str) -> str:
    """ Обрезать фрагмент акта, найти 'БПР' или 'ВР', добавить поле release в result """

    dct = json.loads(result)

    # если документ - не акт, ИЛИ если нет ТБ сделок, не запускаем процесс + добавляем в result пустое поле 'release'
    if (dct['Тип документа'] != 'акт' or
            bool(dct.get('Номера таможенных сделок', False)) is False):
        dct['release'] = ''
        return json.dumps(dct, ensure_ascii=False, indent=4)

    # обрезаем и сохраняем фрагмент с релизом
    first_page_image_file = os.path.join(current_folder, 'extra_data', 'first_page_image.jpg')
    release_save_path = release_crop_and_save(first_page_image_file)

    # получаем ответ от openai, добавляем в result поле 'release'
    response = run_chat(release_save_path, prompt=release_prompt, response_format=release_response_format)
    release = json.loads(response)['release']
    if release == "БЕЗ ПРАВА РЕАЛИЗАЦИИ":
        dct["release"] = "БПР"
    else:
        dct["release"] = "ВР"

    return json.dumps(dct, ensure_ascii=False, indent=4)

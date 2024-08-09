import os
import sys
import json
import msvcrt
from glob import glob

config = dict()

if getattr(sys, 'frozen', False):  # в сборке
    config['BASE_DIR'] = os.path.dirname(sys.executable)
    config['POPPLER_PATH'] = os.path.join(sys._MEIPASS, 'poppler')
    config['magick_exe'] = os.path.join(sys._MEIPASS, 'magick', 'magick.exe')
else:
    config['BASE_DIR'] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config['POPPLER_PATH'] = r'C:\Program Files\poppler-22.01.0\Library\bin'
    config['magick_exe'] = 'magick'  # или полный путь до ...magick.exe файла, если не добавлено в Path

config['GPTMODEL'] = 'gpt-4o-2024-08-06'
config['POPPLER_PATH'] = r'C:\Program Files\poppler-22.01.0\Library\bin'

config['json_struct'] = '{"Номер документа": "","Номера контейнеров": [] ,"Номер коносамента": ""}'
config['system_prompt'] = f"""
Ты бот, анализирующий документы (фитосанитарный контроль грузов, перевозимых по морю).
Ты анализируешь документ следующим образом:
1. Находишь номер документа (акта), который состоит из 15 цифр.
2. В графе 'Транспортные средства' находишь номера контейнеров строго в формате [A-Z]{{3}}U\s?[0-9]{{7}}.
3. В графе 'Транспортные средства' после номеров контейнеров находишь номер коносамента (к/с), который состоит из [a-zA-Z0-9].
4. Если "Номер контейнера" не является [A-Z]{{3}}U\s?[0-9]{{7}}, он перемещается в "Номер коносамента"
""".strip()

JSON_SCHEMA = {
    "name": "document",
    "schema": {
        "type": "object",
        "properties": {
            "Номер документа": {
                "type": "string"
            },
            "Номера контейнеров": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "Судно": {
                "type": "string"
            },
            "Номер коносамента": {
                "type": "string"
            }
        },
        "required": ["Номер документа", "Номера контейнеров", "Судно", "Номер коносамента"],
        "additionalProperties": False
    },
    "strict": True
}

config['response_format'] = {"type": "json_schema", "json_schema": JSON_SCHEMA}

if __name__ == '__main__':
    for k, v in config.items():
        if k not in ['unique_comments_dict']:
            print('-' * 50)
            print(k)
            print(v)
            if k == 'json_struct':
                try:
                    json.loads(v)
                except json.decoder.JSONDecodeError:
                    print("Нарушена структура json")
                    break

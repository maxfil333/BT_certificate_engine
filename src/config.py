import os
import sys
import json
import msvcrt
from glob import glob
from dotenv import load_dotenv

load_dotenv()

config = dict()

config['user_1C'] = os.getenv('user_1C')
config['password_1C'] = os.getenv('password_1C')
config['V83_CONN_STRING'] = f"Srvr=kappa; Ref=CUP; Usr={config['user_1C']}; Pwd={config['password_1C']}"

if os.path.exists(path_file := os.path.join('..', 'paths.json')):
    with open(path_file, 'r', encoding='utf-8') as file:
        dct = json.load(file)
        config['BASE_DIR'] = dct['BASE_DIR']
else:
    if getattr(sys, 'frozen', False):  # в сборке
        config['BASE_DIR'] = os.path.dirname(sys.executable)
        config['POPPLER_PATH'] = os.path.join(sys._MEIPASS, 'poppler')
        config['magick_exe'] = os.path.join(sys._MEIPASS, 'magick', 'magick.exe')
    else:
        config['BASE_DIR'] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config['POPPLER_PATH'] = r'C:\Program Files\poppler-22.01.0\Library\bin'
        config['magick_exe'] = 'magick'  # или полный путь до ...magick.exe файла, если не добавлено в Path

config['IN'] = os.path.join(config['BASE_DIR'], 'IN')
config['EDITED'] = os.path.join(config['BASE_DIR'], 'EDITED')
config['OUT'] = os.path.join(config['BASE_DIR'], 'OUT')
config['untitled'] = os.path.join(config['OUT'], '0_Нераспознанные')
os.makedirs(config['untitled'], exist_ok=True)

print(f"IN: {config['IN']}\nEDITED: {config['EDITED']}\nOUT: {config['OUT']}")

config['GPTMODEL'] = 'gpt-4o-2024-08-06'
config['POPPLER_PATH'] = r'C:\Program Files\poppler-22.01.0\Library\bin'

config['certificate_system_prompt'] = f"""
Ты бот, анализирующий документы (фитосанитарный контроль грузов, перевозимых по морю).
Ты анализируешь документ следующим образом:
1. Определяешь тип документа.
2. Находишь номер документа. Если тип = "акт", то номер документа состоит из 15 цифр.
3. Находишь все номера контейнеров строго в формате [A-Z]{{3}}U\s?[0-9]{{7}}.
4. В графе 'Транспортные средства' после номеров контейнеров находишь один номер коносамента (к/с), который состоит из [a-zA-Z0-9].
5. Если к этому моменту номер коносамента не найден, проверь найденные контейнеры. Если какой-то из них не соответствует [A-Z]{{3}}U\s?[0-9]{{7}}, то это номер коносамента.
6. Если информация не найдена, впиши "".
""".strip()

CERT_JSON_SCHEMA = {
    "name": "document",
    "schema": {
        "type": "object",
        "properties": {
            "Тип документа": {
                "type": "string",
                "description": "Коносамент или Акт Фитосанитарного Контроля или Заключение или Протокол",
                "enum": ["коносамент", "акт", "заключение", "протокол"]
            },
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
                "description": "Номер коносамента | bill of lading number | b/l number | Waybill number",
                "type": "string"
            }
        },
        "required": ["Тип документа", "Номер документа", "Номера контейнеров", "Судно", "Номер коносамента"],
        "additionalProperties": False
    },
    "strict": True
}

config['certificate_response_format'] = {"type": "json_schema", "json_schema": CERT_JSON_SCHEMA}

config['appendix_system_prompt'] = f"""
Ты бот, анализирующий документы (фитосанитарный контроль грузов, перевозимых по морю).
Ты анализируешь документ следующим образом:
1. Для каждой позиции находишь номера фитосанитарных сертификатов и дату.
2. Если информация не найдена, впиши "".
""".strip()

APDX_JSON_SCHEMA = {
    "name": "document",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "documents": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "Номера документов": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "Дата": {
                            "type": "string"
                        }
                    },
                    "required": ["Номера документов", "Дата"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["documents"],
        "additionalProperties": False
    }
}

config['appendix_response_format'] = {"type": "json_schema", "json_schema": APDX_JSON_SCHEMA}

if __name__ == '__main__':
    for k, v in config.items():
        if k not in ['unique_comments_dict']:
            print('-' * 50)
            print(k)
            print(v)

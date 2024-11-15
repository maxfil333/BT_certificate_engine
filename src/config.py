import os
import sys
import json
from dotenv import load_dotenv
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties


load_dotenv()
config = dict()

if getattr(sys, 'frozen', False):  # в сборке
    config['PROJECT_DIR'] = os.path.dirname(sys.executable)
else:
    config['PROJECT_DIR'] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ___________________________ 1C | COM ___________________________
config['user_1C'] = os.getenv('user_1C')
config['password_1C'] = os.getenv('password_1C')
config['V83_CONN_STRING'] = f"Srvr=kappa; Ref=CUP; Usr={config['user_1C']}; Pwd={config['password_1C']}"

# ___________________________ BASE DIR ___________________________
DEBUG_JSON = os.path.join(config['PROJECT_DIR'], 'DEBUG.json')

if os.path.exists(DEBUG_JSON):  # TEST
    config['DEBUG'] = True
    with open(DEBUG_JSON, 'r', encoding='utf-8-sig') as file:
        config['BASE_DIR'] = json.load(file)['BASE_DIR']
    config['TOKEN'] = os.getenv('TEST_TOKEN')
    config['channel_id'] = os.getenv('test_channel_id')
    print(f"\"DEBUG.json\" was found in: {DEBUG_JSON}.\nBASE DIR = {config['BASE_DIR']}\n")

else:  # PROD
    config['DEBUG'] = False
    config['BASE_DIR'] = r"\\10.10.0.3\Docs\CUSTOM\0 Документы с Районов"
    config['TOKEN'] = os.getenv('TOKEN')
    config['channel_id'] = os.getenv('channel_id')
    print(f"No \"DEBUG.json\" was found.\nBASE DIR = {config['BASE_DIR']}\n")

config['IN'] = os.path.join(config['BASE_DIR'], 'IN')
config['EDITED'] = os.path.join(config['BASE_DIR'], 'EDITED')
config['OUT'] = os.path.join(config['BASE_DIR'], 'OUT')
config['untitled'] = os.path.join(config['OUT'], '0_Нераспознанные')
print(f"IN: {config['IN']}\nEDITED: {config['EDITED']}\nOUT: {config['OUT']}")

# __________ BOT PARAMETERS __________
config['bot'] = Bot(token=config['TOKEN'], default=DefaultBotProperties(parse_mode='HTML'))

# ___________________________ poppler | magick ___________________________
config['magick_opt'] = '-colorspace Gray -quality 100 -units PixelsPerInch -density 350'.split(' ')

if getattr(sys, 'frozen', False):  # в сборке
    config['POPPLER_PATH'] = os.path.join(sys._MEIPASS, 'poppler')
    config['magick_exe'] = os.path.join(sys._MEIPASS, 'magick', 'magick.exe')
else:
    config['POPPLER_PATH'] = r'C:\Program Files\poppler-24.07.0\Library\bin'
    config['magick_exe'] = 'magick'  # или полный путь до ...magick.exe файла, если не добавлено в Path

# ___________________________ GPT | PROMPTS | PARAMS ___________________________
config['GPTMODEL'] = 'gpt-4o-2024-08-06'

config['certificate_system_prompt'] = f"""
Ты бот, анализирующий документы (фитосанитарный контроль грузов, перевозимых по морю).
Ты анализируешь документ следующим образом:
1. Определяешь тип документа.
2. Находишь номер документа. Если тип = "акт", то номер документа состоит из 15 цифр.
3. Находишь все номера контейнеров строго в формате [A-Z]{{3}}U\s?[0-9]{{7}}.
4. В графе 'Транспортные средства' после номеров контейнеров находишь один номер коносамента (к/с), который состоит из [a-zA-Z0-9].

Пример 1: "K/C:BS038RS084(1K:CICU4110810)"
  {{"Номера контейнеров": ['CICU4110810'], "Номер коносамента": "BS038RS084"}}
Пример 2: "КОНТЕЙНЕР:К/С:MLIBR002942(2 КОНТ.HPCU4589907,MODU1034477) HONG PROSPERITY"
  {{"Номера контейнеров": ["HPCU4589907","MODU1034477"], "Номер коносамента": "MLIBR002942"}}
Пример 3: "К/С_RU06588 COOL SPIRIT"
  {{"Номера контейнеров": [], "Номер коносамента": "RU06588"}}
Пример 4: "КОНТЕЙНЕР:К/С:MUGTLL2401348 1КОНТ.TRLU7102315 ARINA"
  {{"Номера контейнеров": ["TRLU7102315"], "Номер коносамента": "MUGTLL2401348"}}

5. Если к этому моменту номер коносамента не найден, проверь найденные контейнеры. Если какой-то из них не соответствует [A-Z]{{3}}U\s?[0-9]{{7}}, то это номер коносамента.
6. Если информация не найдена, впиши "".
""".strip()

# TODO: ОТФИЛЬТРОВАТЬ КОНТЕЙНЕРЫ НЕ ПОДХОДЯЩИЕ ПОД РЕГУЛЯРКУ

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
                "description": "[A-Z]{3}U[0-9]{7}",
                "items": {
                    "type": "string"
                }
            },
            "Судно": {
                "type": "string"
            },
            "Номер коносамента": {
                "description": "Номер коносамента | К/С | bill of lading number | b/l number | Waybill number | B/L №",
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

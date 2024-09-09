import os
import re
import json
import openai
from openai import OpenAI
import inspect
from PIL import Image
from time import perf_counter
from dotenv import load_dotenv

from config import config
from logger import logger
from utils import extract_text_with_fitz, switch_to_latin
from utils import base64_encode_image, base64_encode_pil

start = perf_counter()
load_dotenv()
openai.api_key = os.environ.get("OPENAI_API_KEY")
ASSISTANT_ID = os.environ.get("ASSISTANT_ID")
client = OpenAI()


def certificate_local_postprocessing(response, connection):
    dct = json.loads(response)
    dct['Номера сделок'] = []
    dct['Номера таможенных сделок'] = []
    dct['Номера фсс'] = '%None%'

    if len(dct['Номер коносамента']) < 5:
        dct['Номер коносамента'] = ''

    if connection and dct['Номер коносамента']:
        conos_id = dct['Номер коносамента']
        trans_number = connection.InteractionWithExternalApplications.TransactionNumberFromBillOfLading(conos_id)
        customs_trans = connection.InteractionWithExternalApplications.CustomsTransactionFromBillOfLading(conos_id)
        dct['Номера сделок'] = [x.strip() for x in trans_number.strip("|").split("|") if x.strip()]
        dct['Номера таможенных сделок'] = [x.strip() for x in customs_trans.strip("|").split("|") if x.strip()]

    return json.dumps(dct, ensure_ascii=False, indent=4)


def appendix_local_postprocessing(response, connection):
    dct = json.loads(response)
    dct['result'] = {'fcc_numbers': None, "transaction_numbers": None}
    fcc_numbers = []
    for pos in dct['documents']:
        doc_numbers = pos["Номера документов"]
        for number in doc_numbers:
            if number not in fcc_numbers:
                fcc_numbers.append(number)
    dct['result']['fcc_numbers'] = fcc_numbers

    tr_numbers = []
    if fcc_numbers:
        for number in fcc_numbers:
            if True:  # try in english
                number_en = switch_to_latin(number)
                customs_trans = connection.InteractionWithExternalApplications.CustomsTransactionNumberFromBrokerDocument(
                    number_en)
            if not customs_trans:  # then try in russian
                number_ru = switch_to_latin(number, reverse=True)
                customs_trans = connection.InteractionWithExternalApplications.CustomsTransactionNumberFromBrokerDocument(
                    number_ru)
            if customs_trans:  # if some result
                customs_trans = [x.strip() for x in customs_trans.strip("|").split("|") if x.strip()]
                tr_numbers.extend(customs_trans)

        dct['result']['transaction_numbers'] = list(set(tr_numbers))
    return json.dumps(dct, ensure_ascii=False, indent=4)


# ___________________________ CHAT ___________________________

def run_chat(*img_paths: str, prompt, response_format, detail='high', text_mode_content: str | None = None) -> str:
    """
    :param img_paths: images paths
    :param prompt: system prompt
    :param response_format: {"type": "json_schema", "json_schema": <JSON_SCHEMA>}
    :param detail: image quality
    :param text_mode_content: if not None, text_content for messages.user.content
    :return: json-string
    """

    if text_mode_content:
        content = text_mode_content
    else:
        content = []
        for img_path in img_paths:
            d = {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_encode_pil(Image.open(img_path))}",
                              "detail": detail}
            }
            content.append(d)

    response = client.chat.completions.create(
        model=config['GPTMODEL'],
        temperature=0.1,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": content}
        ],
        max_tokens=200,
        response_format=response_format
    )
    logger.print('chat model:', response.model)
    logger.print(f'time: {perf_counter() - start:.2f}')
    logger.print(f'completion_tokens: {response.usage.completion_tokens}')
    logger.print(f'prompt_tokens: {response.usage.prompt_tokens}')
    logger.print(f'total_tokens: {response.usage.total_tokens}')

    response = response.choices[0].message.content
    return response

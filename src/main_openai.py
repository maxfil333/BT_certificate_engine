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
from utils import extract_text_with_fitz
from utils import base64_encode_image, base64_encode_pil

start = perf_counter()
load_dotenv()
openai.api_key = os.environ.get("OPENAI_API_KEY")
ASSISTANT_ID = os.environ.get("ASSISTANT_ID")
client = OpenAI()


def local_postprocessing(response, connection):
    dct = json.loads(response)
    dct['Номер сделки'] = ''
    dct['Номер таможенной сделки'] = ''

    if len(dct['Номер коносамента']) < 5:
        dct['Номер коносамента'] = ''

    if connection and dct['Номер коносамента']:
        conos_id = dct['Номер коносамента']
        trans_number = connection.InteractionWithExternalApplications.TransactionNumberFromBillOfLading(conos_id)
        customs_trans = connection.InteractionWithExternalApplications.CustomsTransactionFromBillOfLading(conos_id)
        dct['Номер сделки'] = trans_number
        dct['Номер таможенной сделки'] = customs_trans

    return json.dumps(dct, ensure_ascii=False, indent=4)


# ___________________________ CHAT ___________________________

def run_chat(*img_paths: str, detail='high', text_mode=False, connection=None) -> str:
    if text_mode:
        if len(img_paths) != 1:
            logger.print("ВНИМАНИЕ! На вход run_chat пришли pdf-файлы в количестве != 1")
        content = extract_text_with_fitz(img_paths[0])
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
            {"role": "system", "content": config['system_prompt']},
            {"role": "user", "content": content}
        ],
        max_tokens=200,
        response_format=config['response_format']
    )
    logger.print('chat model:', response.model)
    logger.print(f'time: {perf_counter() - start:.2f}')
    logger.print(f'completion_tokens: {response.usage.completion_tokens}')
    logger.print(f'prompt_tokens: {response.usage.prompt_tokens}')
    logger.print(f'total_tokens: {response.usage.total_tokens}')

    response = response.choices[0].message.content
    return local_postprocessing(response=response, connection=connection)


# ___________________________ ASSISTANT ___________________________

def run_assistant(file_path):
    assistant = client.beta.assistants.retrieve(assistant_id=ASSISTANT_ID)
    message_file = client.files.create(file=open(file_path, "rb"), purpose="assistants")
    # Create a thread and attach the file to the message
    thread = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": " ",
                "attachments": [{"file_id": message_file.id, "tools": [{"type": "file_search"}]}],
            }
        ]
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id, assistant_id=assistant.id
    )
    if run.status == 'completed':
        logger.print('assistant model:', assistant.model)
        logger.print(f'file_path: {file_path}')
        logger.print(f'time: {perf_counter() - start:.2f}')
        logger.print(f'completion_tokens: {run.usage.completion_tokens}')
        logger.print(f'prompt_tokens: {run.usage.prompt_tokens}')
        logger.print(f'total_tokens: {run.usage.total_tokens}')

    messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))
    response = messages[0].content[0].text.value
    return local_postprocessing(response)

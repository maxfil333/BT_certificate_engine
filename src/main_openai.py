import os
import openai
from PIL import Image
from openai import OpenAI
from time import perf_counter
from dotenv import load_dotenv

from src.logger import logger
from src.config import config
from src.utils import base64_encode_pil


start = perf_counter()
load_dotenv()
openai.api_key = os.environ.get("OPENAI_API_KEY")
ASSISTANT_ID = os.environ.get("ASSISTANT_ID")
client = OpenAI()


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
    start = perf_counter()
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
    logger.print(f'cached_tokens: {response.usage.prompt_tokens_details}')
    logger.print(f'prompt_tokens: {response.usage.prompt_tokens}')
    logger.print(f'total_tokens: {response.usage.total_tokens}')

    response = response.choices[0].message.content
    return response

import os
from main_openai import run_chat

from config import config


def main():
    folder = os.path.join(config['BASE_DIR'], r'data_random_6')
    img_file = os.path.join(folder, r'1.jpg')

    result = run_chat(img_file)
    print('result:')
    print(result)


if __name__ == '__main__':
    main()

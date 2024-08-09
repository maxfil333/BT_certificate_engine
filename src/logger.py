import os


class Logger:
    def __init__(self):
        self.data = []

    def print(self, *args, **kwargs):
        # Извлекаем параметры sep и end из kwargs, если они есть, или задаем значения по умолчанию
        sep = kwargs.pop('sep', ' ')
        end = kwargs.pop('end', '\n')
        # Формируем сообщение
        message = sep.join(map(str, args)) + end
        # Выводим сообщение в консоль
        print(message, **kwargs, end='')
        # Сохраняем сообщение в data
        self.data.append(message)

    def save(self, log_folder):
        # Записываем логи в файл
        log_file = os.path.join(log_folder, 'log.log')
        with open(log_file, 'a', encoding='utf-8') as file:
            file.writelines(self.data)


logger = Logger()

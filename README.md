## Режим запуска
- если в корневой директории есть файл **DEBUG.json** (TEST):
```
config['BASE_DIR'] = json.load(file)['BASE_DIR']
config['TOKEN'] = os.getenv('TEST_TOKEN')
config['channel_id'] = os.getenv('test_channel_id')
```
- если нет (PROD):
```
config['TOKEN'] = os.getenv('TOKEN')
config['channel_id'] = os.getenv('channel_id')
config['BASE_DIR'] = r"\\10.10.0.3\Docs\..."
```

## Настройка COM соединения 
- Администрирование->Службы компонентов. Компьютеры->Мой Компьютер->Приложения COM+. Создать новое приложение — серверное приложение — название V82_COMConnector. После, на вкладке «компонетны» созданного приложения добавить новый компонент: (установка новых компонентов) и указать на файлик comcntr.dll в комплекте 1С.<br> ```"C:\Program Files\1cv8\8.3.21.1895\bin\comcntr.dll"``` или <br> ```"C:\Program Files (x86)\1cv8\8.3.21.1895\bin\comcntr.dll")```
- (cmd от имени админа) <br>
```regsvr32 "C:\Program Files\1cv8\8.3.21.1895\bin\comcntr.dll"```

## Для запуска на Windows Server

- install git
- install python 3.11.9
- install Visual C++ Redistributable for Visual Studio 2015
- git clone https://github.com/maxfil333/BT_certificate_bot.git 
- python -m venv venv
- venv\Scripts\activate
- pip install -r requirements.txt
- add .env file
- download poppler https://github.com/oschwartz10612/poppler-windows/releases/
- unpack and place anywhere
- replace in **src/config.py** <br>```config['POPPLER_PATH'] = r'C:\Program Files\poppler-24.07.0\Library\bin'``` 
<br>with your poppler path (pay attention to the poppler version in path)
- delete DEBUG.json file
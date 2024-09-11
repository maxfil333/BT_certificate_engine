## Для запуска на Windows Server

- установить python 3.11.9, git
- установить Visual C++ Redistributable for Visual Studio 2015
- скачать poppler https://github.com/oschwartz10612/poppler-windows/releases/
- распаковать и поместить в любое место
- поменять в **src/config.py** <br>```config['POPPLER_PATH'] = r'C:\Program Files\poppler-24.07.0\Library\bin'``` <br>на ваш путь (обратите внимание на версию poppler)
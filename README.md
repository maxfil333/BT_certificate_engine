## Настройка COM соединения 
- Администрирование->Службы компонентов. Компьютеры->Мой Компьютер->Приложения COM+. Создать новое приложение — серверное приложение — название V82_COMConnector. После, на вкладке «компонетны» созданного приложения добавить новый компонент: (установка новых компонентов) и указать на файлик comcntr.dll в комплекте 1С.<br> ```"C:\Program Files\1cv8\8.3.21.1895\bin\comcntr.dll"``` или <br> ```"C:\Program Files (x86)\1cv8\8.3.21.1895\bin\comcntr.dll")```
- (cmd от имени админа) <br>
```regsvr32 "C:\Program Files\1cv8\8.3.21.1895\bin\comcntr.dll"```

## Для запуска на Windows Server

- установить python 3.11.9, git
- установить Visual C++ Redistributable for Visual Studio 2015
- скачать poppler https://github.com/oschwartz10612/poppler-windows/releases/
- распаковать и поместить в любое место
- поменять в **src/config.py** <br>```config['POPPLER_PATH'] = r'C:\Program Files\poppler-24.07.0\Library\bin'``` <br>на ваш путь (обратите внимание на версию poppler)
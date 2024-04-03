# homework_bot
Telegram-бот, который обращается к API сервиса Я.Практикум и узнает статус домашней работы.

### Технологии:

[![name badge](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![name badge](https://img.shields.io/badge/Django-3776AB?logo=django&logoColor=white)](https://docs.djangoproject.com/en/4.2/releases/3.2/)
[![name badge](https://img.shields.io/badge/Telegram-3776AB?logo=telegram&logoColor=white)](https://core.telegram.org/)

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/Anna9449/homework_bot.git
```

```
cd homework_bot
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

* Если у вас Linux/macOS

    ```
    source env/bin/activate
    ```

* Если у вас windows

    ```
    source env/scripts/activate
    ```

```
python3 -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Создать файл .env и заполните его своими данными, пример: 

```
PRACTICUM_TOKEN=pract_token # Токен профиля на Я.Практикуме
TELEGRAM_TOKEN=token # Токен телеграм-бота
TELEGRAM_CHAT_ID=id # id своего аккаунта
```

Запустить проект:

```
python homework.py
```


### Автор
[![name badge](https://img.shields.io/badge/Anna_Pestova-3776AB?logo=github&logoColor=white)](https://github.com/Anna9449)

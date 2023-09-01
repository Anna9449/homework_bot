import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    format='%(asctime)s  [%(levelname)s]  %(message)s',
    level=logging.INFO)


def check_tokens():
    """Проверяем наличие обязательных переменных окружения."""
    token_dict = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    for name, value in token_dict.items():
        if value is None:
            logging.critical(
                f'Отсутствует обязательная переменная окружения: {name}.'
                ' Программа принудительно остановлена.'
            )
            exit()


def send_message(bot, message):
    """"Отправляем сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logging.error(
            f'Cбой при отправке сообщения "{message}" - {error}'
        )
    else:
        logging.debug(
            f'Бот отправил сообщение "{message}"'
        )


def get_api_answer(timestamp):
    """"Отправляем запрос к эндпоинту API-сервиса."""
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS, params={'from_date': timestamp}
        )
        if response.status_code != 200:
            raise ValueError(
                logging.error(
                    f'Эндпоинт {ENDPOINT} недоступен.'
                    f' Код ответа API: {response.status_code}.'
                )
            )
    except requests.exceptions.RequestException as error:
        logging.error(
            f'Эндпоинт {ENDPOINT} недоступен. - {error}'
        )
    return response.json()


def check_response(response):
    """"Проверяем ответ API на наличие ключа 'homeworks'."""
    try:
        homeworks = response['homeworks']
    except KeyError:
        logging.error('Отсутствует ожидаемый ключ "homeworks" в ответе API.')
    if type(homeworks) != list:
        raise TypeError(
            logging.error('Под ключом "homeworks" ожидается список.')
        )


def parse_status(homework):
    """"Получаем статус домашней работы."""
    try:
        homework_name = homework['homework_name']
    except Exception:
        logging.error(
            'Отсутствует ожидаемый ключ "homework_name" в ответе API.'
        )
    try:
        status = homework.get('status')
    except Exception:
        logging.error('Отсутствует ожидаемый ключ "status" в ответе API.')
    try:
        verdict = HOMEWORK_VERDICTS[status]
    except Exception:
        logging.error('Неопознанный статус - {status}')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    d = {}
    check_tokens()
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            homeworks = response.get('homeworks')
            for homework in homeworks:
                homework_name = homework.get('homework_name')
                status = parse_status(homework)
                if d.get(homework_name) != status:
                    send_message(bot, status)
                d[homework_name] = status
        except Exception as error:
            logging.error(f'Сбой в работе программы: {error}')
            exit()
        else:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()

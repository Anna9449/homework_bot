import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import EmptyResponseFromAPIError, InvalidResponseCodeError

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


def check_tokens():
    """Проверяем наличие обязательных переменных окружения."""
    tokens = (
        ('PRACTICUM_TOKEN', PRACTICUM_TOKEN),
        ('TELEGRAM_TOKEN', TELEGRAM_TOKEN),
        ('TELEGRAM_CHAT_ID', TELEGRAM_CHAT_ID)
    )
    available = True
    for name, value in tokens:
        if not value:
            available = False
            logging.critical(
                f'Отсутствует обязательная переменная окружения: {name}.'
            )
    if not available:
        raise ValueError('Программа принудительно остановлена.')


def send_message(bot, message):
    """Отправляем сообщение в Telegram чат."""
    logging.debug(
        'Начинаем отправлять сообщение в чат.'
    )
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.error.TelegramError as error:
        logging.error(
            f'Cбой при отправке сообщения "{message}" - {error}'
        )
        return False
    else:
        logging.debug(
            f'Бот отправил сообщение "{message}"'
        )
        return True


def get_api_answer(timestamp):
    """Отправляем запрос к эндпоинту API-сервиса."""
    params_for_get_api = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': timestamp}
    }
    logging.debug(
        'Начинаем отправлять запрос к эндпоинту API-сервиса: {url}.'
        ' С параметрами: {headers}, {params}.'.format(**params_for_get_api)
    )
    try:
        response = requests.get(
            params_for_get_api.get('url'),
            headers=params_for_get_api.get('headers'),
            params=params_for_get_api.get('params')
        )
        if response.status_code != HTTPStatus.OK:
            message = (
                f'Эндпоинт "{response.url}" недоступен - {response.json}'
                f' Код ответа API: {response.status_code}.'
            )
            logging.error(message)
            raise InvalidResponseCodeError(message)
    except requests.exceptions.RequestException as error:
        ('Эндпоинт {url} c параметрами: {headers}, {params}'
         ).format(**params_for_get_api) + f' - недоступен. - {error}'
    return response.json()


def check_response(response):
    """Проверяем ответ API на наличие ключа 'homeworks'."""
    logging.debug(
        'Проверяем ответ API на наличие ключа "homeworks".'
    )
    if not isinstance(response, dict):
        raise TypeError(
            logging.error('Ответ API ожидается в формате словаря.')
        )
    if 'homeworks' not in response:
        raise EmptyResponseFromAPIError(
            logging.error(
                'Отсутствует ожидаемый ключ "homeworks" в ответе API.'
            )
        )
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError(
            logging.error('Под ключом "homeworks" ожидается список.')
        )
    return homeworks


def parse_status(homework):
    """Получаем статус домашней работы."""
    logging.debug(
        'Получаем статус домашней работы.'
    )
    if 'homework_name' not in homework:
        raise KeyError(
            logging.error(
                'Отсутствует ожидаемый ключ "homework_name" в ответе API.'
            )
        )
    homework_name = homework.get('homework_name')
    if 'status' not in homework:
        raise KeyError(
            logging.error(
                'Отсутствует ожидаемый ключ "status" в ответе API.'
            )
        )
    status = homework.get('status')
    if status not in HOMEWORK_VERDICTS:
        raise ValueError(
            logging.error('Неопознанный статус - {status}')
        )
    verdict = HOMEWORK_VERDICTS.get(status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = 0
    prev_report = ''
    current_report = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                homework = homeworks[0]
                status = parse_status(homework)
                current_report = status
            else:
                current_report = 'Нет новых статусов.'
            if current_report != prev_report:
                if send_message(bot, status):
                    prev_report = current_report
                    timestamp = response.get('current_date', 0)
            else:
                logging.debug(
                    'Нет новых статусов.'
                )

        except EmptyResponseFromAPIError as error:
            logging.error(f'Пустой ответ от API - {error}')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            current_report = message
            logging.error(message)
            if current_report != prev_report:
                send_message(bot, current_report)
                prev_report = current_report
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logger = logging.getLogger('log')
    logger.setLevel(logging.INFO)
    fmtstr = ('%(asctime)s  [%(levelname)s] - (%(funcName)s(%(lineno)d)'
              ' -  %(message)s')
    handler_term = logging.StreamHandler()
    handler_file = logging.FileHandler(__file__ + '.log', encoding='utf-8')
    formatter = logging.Formatter(fmtstr)
    handler_term.setFormatter(formatter)
    handler_file.setFormatter(formatter)
    logger.addHandler(handler_term)
    logger.addHandler(handler_file)
    main()

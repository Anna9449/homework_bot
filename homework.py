import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv
from http import HTTPStatus

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
    token_dict = (
        ('PRACTICUM_TOKEN', PRACTICUM_TOKEN),
        ('TELEGRAM_TOKEN', TELEGRAM_TOKEN),
        ('TELEGRAM_CHAT_ID', TELEGRAM_CHAT_ID)
    )
    available = True
    for name, value in token_dict:
        if not value:
            available = False
            logging.critical(
                f'Отсутствует обязательная переменная окружения: {name}.'
            )
    if not available:
        ValueError('Программа принудительно остановлена.')
        exit()


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
    params_dict = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': timestamp}
    }
    logging.debug(
        'Начинаем отправлять запрос к эндпоинту API-сервиса.'
    )
    url, headers, params = [* params_dict.values()]
    try:
        response = requests.get(
            url,
            headers=headers,
            params=params
        )
        if response.status_code != HTTPStatus.OK:
            raise requests.exceptions.InvalidResponseCode(
                logging.error(
                    f'Эндпоинт {url} недоступен - {response.text}'
                    f' Код ответа API: {response.status_code}.'
                )
            )
    except requests.exceptions.RequestException as error:
        (f'Эндпоинт {url} недоступен. - {error}')
    return response.json()


def check_response(response):
    """Проверяем ответ API на наличие ключа 'homeworks'."""
    logging.debug(
        'Проверяем ответ API на наличие ключа "homeworks"'
    )
    if not isinstance(response, dict):
        raise TypeError(
            logging.error('Ответ API ожидается в формате словаря.')
        )
    if 'homeworks' not in response:
        raise requests.exceptions.EmptyResponseFromAPI(
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
        raise KeyError(
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
            if not homeworks:
                raise ValueError(
                    logging.error('У вас нет домашних работ:(')
                )
            homework = homeworks[0]
            status = parse_status(homework)
            current_report = status
            if current_report != prev_report:
                if send_message(bot, status):
                    prev_report = current_report
            else:
                logging.debug(
                    'Нет новых статусов.'
                )
        except requests.exceptions.EmptyResponseFromAPI as error:
            logging.error(f'Пустой ответ от API - {error}')
        except Exception as error:
            logging.error(f'Сбой в работе программы: {error}')
            exit()
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        format=('%(asctime)s  [%(levelname)s] - (%(funcName)s(%(lineno)d)'
                ' -  %(message)s'),
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler_term = logging.StreamHandler()
    handler_file = logging.FileHandler(__file__ + '.log')
    logger.addHandler(handler_term)
    logger.addHandler(handler_file)
    main()

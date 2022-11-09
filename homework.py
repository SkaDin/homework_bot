import logging
import time
import os
import sys
from http import HTTPStatus

import telegram
import requests


from exceptions import (
    EnvVariablesNotAvailable, UnavailableApi, UnknownHomeworkStatus,
    WrongAnswerFormat
)

from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def send_message(bot, message):
    """Функция отправления сообщения ботом."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info('Сообщение в телеграмм отправлено!')
    except telegram.error.TelegramError as error:
        logger.error(f'Сбой при отправке сообщения! {error}')


def get_api_answer(current_timestamp):
    """Функция делает запрос к API ЯндексПрактикума."""
    try:
        timestamp = current_timestamp or int(time.time())
        params = {'from_date': timestamp}
        logging.info('Отправляю запрос к API ЯндексПрактикума.')
        response = requests.get(
            url=ENDPOINT,
            headers=HEADERS,
            params=params
        )
        if response.status_code == HTTPStatus.OK:
            logging.info(f'Ответ от API:{response.json()}')
            return response.json()
        else:
            logger.error('Сбой при запросе к эндпоинту!')
            raise UnavailableApi('Сбой при запросе к API.')
    except Exception as error:
        logger.error('Сбой при запросе к эндпоинту!')
        raise UnavailableApi(f'Сбой при запросе к API!{error}')


def check_response(response):
    """Функция проверяет корректность запроса к API."""
    if isinstance(response, dict) and isinstance(response['homeworks'], list):
        logger.info('Формат соответсвует ожидаемому.')
        return response['homeworks']
    logger.error('Формат не соответсвует ожидаемому!')
    raise WrongAnswerFormat


def parse_status(homework):
    """Функция для парсинга ДЗ."""
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except KeyError as error:
        logger.error(f'Неожиданный статус работы!{error}')
        raise UnknownHomeworkStatus


def check_tokens():
    """Функция проверки переменных окружения."""
    return all([
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID
    ])


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    api_error_count = 0
    while True:
        try:
            if check_response():
                logger.info('Все переменные окружения достпуны.')
                response = get_api_answer(current_timestamp)
                homeworks = check_response(response)
                if len(homeworks) > 0:
                    for homework in homeworks:
                        message = parse_status(homework)
                        send_message(bot, message)
                else:
                    logger.debug('Нет изменений в статусах работ!')
                current_timestamp = response.get(
                    'current_date', current_timestamp
                )
            else:
                logger.critical('Недоступны переменные окружения!')
                sys.exit('Недоступны переменные окружения!')
        except Exception as error:
            message = f'Сбой в работе программы: {error}.'
            if (not isinstance(error, EnvVariablesNotAvailable)
                    and not isinstance(error, telegram.error.TelegramError)):
                if isinstance(error, UnavailableApi):
                    if api_error_count == 0:
                        send_message(bot, message)
                        api_error_count += 1
        else:
            send_message(bot, message)

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()

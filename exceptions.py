class UnavailableApi(Exception):
    """Исключение при недоступном API Практикума."""
    pass

class WrongAnswerFormat(TypeError):
    """Исключение при неправильном формате сообщения."""
    pass


class UnknownHomeworkStatus(KeyError):
    """Исключение при неизвестном статусе ДЗ."""
    pass

class ProgramMalfunction(Exception):
    """Сбой в работе программы"""
    pass

class EnvVariablesNotAvailable(Exception):
    """Исключение при недоступных переменных окружения."""
    pass
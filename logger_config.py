"""
Модуль конфигурирования логгеров
за основу взято https://gist.github.com/chud0/bab1ea18ccba89ab6d1fa4da8a64a249
"""

DEBUG = True

LOGGING_CONF = {
    "disable_existing_loggers": True,
    "version": 1,
    "formatters": {
        "verbose": {
            "format": "%(levelname)-8s %(asctime)s [%(filename)s:%(lineno)d] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "brief": {
            "format": "%(levelname)-8s %(asctime)s %(name)-16s %(message)s",
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "formatter": "verbose",
            "filename": "app.log",
            "encoding": "UTF-8",
            "mode": "a"
        },
    },
    "loggers": {
        "main_logger": {
            "level": "DEBUG" if DEBUG else "INFO",
            "handlers": ["file"],
        },
        "tbot": {
            "level": "DEBUG" if DEBUG else "INFO",
            "handlers": ["file"],
        },
       "moysklad": {
           "level": "DEBUG" if DEBUG else "INFO",
            "handlers": ["file"],
        },
        "google": {
           "level": "DEBUG" if DEBUG else "INFO",
            "handlers": ["file"],
        },
        "utils": {
           "level": "DEBUG" if DEBUG else "INFO",
            "handlers": ["file"],
        },
    },
}
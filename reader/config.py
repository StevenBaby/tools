LOGFILE = "./reader.log"

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s] [%(name)s] [%(process)d] [%(module)s] [%(funcName)s] [%(lineno)d]  [%(levelname)s] | %(message)s'
        },
        'access': {
            'format': '[%(asctime)s] %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            "level": "DEBUG",
        },
        'file': {
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': LOGFILE,
            "level": "INFO",
        },
    },
    'loggers': {
        'crawler': {
            'handlers': ['console', "file", ],
            'level': "INFO",
            'propagate': True,
        },
    },
}

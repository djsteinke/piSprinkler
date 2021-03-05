import logging

import properties


def get_logging_level():
    if properties.log_debug:
        return logging.DEBUG
    elif properties.log_info:
        return logging.INFO
    elif properties.log_warning:
        return logging.WARNING
    else:
        return logging.ERROR

from logging import StreamHandler, Formatter, getLogger, DEBUG, INFO, WARNING, ERROR, CRITICAL


class CustomFormatter(Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "[%(asctime)s] - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        DEBUG: grey + format + reset,
        INFO: grey + format + reset,
        WARNING: yellow + format + reset,
        ERROR: red + format + reset,
        CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = Formatter(log_fmt)
        return formatter.format(record)


# create logger with 'spam_application'
logger = getLogger("danafx")
logger.setLevel(DEBUG)

# create console handler with a higher log level
ch = StreamHandler()
ch.setLevel(DEBUG)

ch.setFormatter(CustomFormatter())

logger.addHandler(ch)

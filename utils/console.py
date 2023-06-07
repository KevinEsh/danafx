from atexit import register
from datetime import datetime
from logging import StreamHandler, Formatter, getLogger, DEBUG, INFO, WARNING, ERROR, CRITICAL

class CustomFormatter(Formatter):
    """
    CustomFormatter class for handling custom formats in logging.
    """

    # Define colors
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    blue = "\x1b[34m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    # Define log format
    format = "[%(asctime)s] - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    
    # Define format for each log level
    FORMATS = {
        DEBUG: blue + format + reset,
        INFO: format,
        WARNING: yellow + format + reset,
        ERROR: red + format + reset,
        CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        """
        Format the log record and write to file.
        """
        # Get the format for the current log level
        log_fmt = self.FORMATS.get(record.levelno)

        # Write the file record
        file_record = self.file_formatter.format(record)
        self.file.write(file_record + "\n")

        # Return the console record
        console_formatter = Formatter(log_fmt)
        return console_formatter.format(record)
    
    def set_file(self):
        """
        Set up the log file.
        """
        # Open the log file with today's date
        today = datetime.now().strftime('%Y-%m-%d')
        self.file = open(f'logs/{today}.log', "a")

        # Set up the file formatter
        log_fmt = self.FORMATS.get(INFO)
        self.file_formatter = Formatter(log_fmt)

        # Register the file close method to be called at exit
        register(self.file.close)


def get_logger():
    """
    Get a logger with custom settings.
    """
    # Create logger
    logger = getLogger("danafx")
    logger.setLevel(DEBUG)

    # Create console handler
    ch = StreamHandler()

    # Set up the custom formatter
    cf = CustomFormatter()
    cf.set_file()

    # Add the custom formatter to the console handler
    ch.setFormatter(cf)

    # Add the console handler to the logger
    logger.addHandler(ch)

    # Return the logger
    return logger

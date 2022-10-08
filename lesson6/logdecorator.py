import logging
import sys
from functools import wraps
import inspect


def log(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        logger.debug(f"Функция {func.__name__}() вызвана из функции {inspect.stack()[1].function}()")
        return func(*args, **kwargs)
    return decorated


@log
def testfunc():
    """Ничего не делает"""
    pass


def main():
    testfunc()


if __name__ == "__main__":
    # Configure main logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format="%(asctime)s %(message)s",
    )
    # Initialize logger
    logger = logging.getLogger()
    # Display help for decorated function
    logger.debug("Имя декорированной функции testfunc(): %s", testfunc.__name__)
    logger.debug("Документация декорированной функции testfunc(): %s", testfunc.__doc__)
    # Call decorated function
    main()

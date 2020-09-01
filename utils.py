import os
import re
import logging

logger = logging.Logger('happypi', logging.FATAL)


def make_dir(path):
    path = os.path.abspath(path)
    try:
        if not os.path.exists(path):
            os.mkdir(path)
        elif not os.path.isdir(path):
            logger.error(f'{path} is not a dir')
            return -1
    except Exception:
        logger.fatal(f'Cannot create dir: {path}')
        return -1
    else:
        return 0


def get_package_name(package_line):
    info = re.split(
        r'([\w_-]+)(([<>=]=)([\d\.]+\d+)(,([<>=]=)([\d\.]+\d+))?)?', package_line)
    return info[1]


config = {
    'PYPI_SRC': 'https://pypi.tuna.tsinghua.edu.cn/simple',
    'PACKAGE_ROOT': os.path.join(os.path.dirname(__file__), 'packages'),
    'PYPI_JSON_API': 'https://pypi.org/pypi/{}/json'
}

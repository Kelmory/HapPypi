import argparse
import os
import re
import sys
from urllib.parse import urljoin

import gevent
from gevent.monkey import patch_all

patch_all()

import requests

import logging
from bs4 import BeautifulSoup



config = {
    'PYPI_SRC': 'https://pypi.tuna.tsinghua.edu.cn/simple',
    'PACKAGE_ROOT': os.path.join(os.path.dirname(__file__), 'packages')
}

def make_dir(path):
    path = os.path.abspath(path)
    try:
        if not os.path.exists(path):
            os.mkdir(path)
        elif not os.path.isdir(path):
            return -1
    except Exception as e:
        logging.log(logging.FATAL, f'Cannot create dir: {path}')
        return -1
    else:
        return 0


def download_package(package, dist_url, name):
    try:
        response = requests.get(dist_url)
    except Exception:
        logging.log(logging.ERROR, f'File: failed to download {name}')
        return -1
    else:
        try:
            with open(os.path.join(config['PACKAGE_ROOT'], package, name), 'wb+') as f:
                f.write(response.content)
        except Exception:
            logging.log(logging.ERROR, f'File: failed to save {name}.')
        else:
            logging.log(logging.INFO, f'File: saved {package}/{name}')
        return 0


def download_package_dists(package):
    if make_dir(os.path.join(config['PACKAGE_ROOT'], package)) < 0:
        return -1

    exceptions = []
    url = '/'.join((config['PYPI_SRC'], package))
    try:
        package_dir_response = requests.get(url)
    except:
        logging.log(logging.ERROR, f'Package: failed to get list of {package}')
        return -1

    soup = BeautifulSoup(package_dir_response.content, 'lxml')
    package_dists = tuple(map(lambda x: (urljoin(config['PYPI_SRC'], x.attrs['href']), x.text),
                       soup.findAll('a')))
    jobs = [gevent.spawn(download_package, package, dist_url, name) for (dist_url, name) in package_dists]
    return gevent.joinall(jobs)
                

def download_packages(packages):
    jobs = [gevent.spawn(download_package_dists, package) for package in packages]
    return gevent.joinall(jobs)


def get_package_name(package_line):
    info = re.split('([\w_-]+)(([<>=]=)([\d\.]+\d+)(,([<>=]=)([\d\.]+\d+))?)?', package_line)
    return info[1]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("PIP_LIST", help="the pip-freeze format file for packages to be included")
    parser.add_argument('-d', '--dir', help="the directory for saving packages")
    args = parser.parse_args()

    try:
        with open(args.PIP_LIST, 'r+') as f:
            packages = f.readlines()
    except:
        sys.exit(-1)

    packages = tuple(map(get_package_name, packages))    
 
    if args.dir:
        config['PACKAGE_ROOT'] = os.path.abspath(args.dir)

    if make_dir(config['PACKAGE_ROOT']) < 0:
        sys.exit(-1)

    download_packages(packages)

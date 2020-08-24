import argparse
import os
import re
import sys
from urllib.parse import urljoin

import gevent
from gevent.monkey import patch_all

# patch_all()

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
            logging.log(logging.ERROR)
            return -1
    except Exception as e:
        logging.fatal(f'Cannot create dir: {path}')
        return -1
    else:
        return 0


def download_package(package, dist_url, name):
    try:
        response = requests.get(dist_url)
    except Exception:
        logging.error(f'File: failed to download {name}')
        return -1
    else:
        try:
            with open(os.path.join(config['PACKAGE_ROOT'], package, name), 'wb+') as f:
                f.write(response.content)
        except Exception:
            logging.error(f'File: failed to save {name}.')
        else:
            logging.info(f'File: saved {package}/{name}')
        return 0


def download_package_dists(package):
    if make_dir(os.path.join(config['PACKAGE_ROOT'], package)) < 0:
        return -1

    exceptions = []
    url = '/'.join((config['PYPI_SRC'], package))
    try:
        package_dir_response = requests.get(url)
    except:
        logging.error(f'Package: failed to get list of {package}')
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
    parser.add_argument('-i', '--index-url', help="optional url for acquiring packages from")
    parser.add_argument('-R', '--recursive', action="store_true", help="download packages in dependency trees recursively")
    args = parser.parse_args()

    try:
        with open(args.PIP_LIST, 'r+') as f:
            packages = f.readlines()
    except:
        logging.log(logging.FATAL, f'Failed to load requirement file {args.PIP_LIST}')
        sys.exit(-1)

    packages = tuple(map(get_package_name, packages))    
 
    if args.dir:
        config['PACKAGE_ROOT'] = os.path.abspath(args.dir)

    if make_dir(config['PACKAGE_ROOT']) < 0:
        sys.exit(-1)

    if args.index_url:
        if not args.index_url.endswith('/simple') and not args.index_url.endswith('/simple/'):
            logging.error(f'URL {args.index_url} has an incorrect route, using {config["PYPI_SRC"]}')
        else:
            config['PYPI_SRC'] = args.index_url

    if args.recursive:
        logging.info('Acquiring packages in dependency tree...')
        cmd = 'python -m pipdeptree -w silence -f -p {}'.format(','.join(packages))
        try:
            with os.popen(cmd) as f:
                lines = f.readlines()
        except:
            logging.error('Failed to get recursive packages')
            y = input('Continue to get packages?[y/n]')
            if y not in ['y', 'Y']:
                sys.exit(0)
        else:
            packages = tuple(map(get_package_name, lines))

    download_packages(packages)

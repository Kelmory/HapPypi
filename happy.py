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
import json


config = {
    'PYPI_SRC': 'https://pypi.tuna.tsinghua.edu.cn/simple',
    'PACKAGE_ROOT': os.path.join(os.path.dirname(__file__), 'packages'),
    'PYPI_JSON_API': 'https://pypi.org/pypi/{}/json'
}

logger = logging.Logger('happypi', logging.INFO)


class RequirementParser(object):
    def __init__(self, initial_packages: list):
        super().__init__()
        
        if not isinstance(initial_packages, (list, tuple)):
            raise TypeError('Initial Packages should be a list or tuple')
        self.to_visit = set(initial_packages)
        self.visited = set()
        self.req_api_base = config['PYPI_JSON_API']

    def get_requirements(self, packages):
        while self.to_visit:
            greenlets = [gevent.spawn(self._get_requirement, package) for package in self.to_visit]
            self.visited.update(self.to_visit)
            self.to_visit.clear()
            gevent.joinall(greenlets)
            print(len(self.visited), self.visited)
        return self.visited     

    def _get_requirement(self, package):
        try:
            response = requests.get(self.req_api_base.format(package))
            requirements = json.loads(response.content)['info']['requires_dist']
        except:
            return None

        if requirements and isinstance(requirements, list):
            requirements = {i.replace(';', ' ').split()[0] for i in requirements}
            requirements = set(filter(lambda x: x not in self.visited, requirements))
            self.to_visit.update(requirements)
        return None

def make_dir(path):
    path = os.path.abspath(path)
    try:
        if not os.path.exists(path):
            os.mkdir(path)
        elif not os.path.isdir(path):
            logger.error(f'{path} is not a dir' )
            return -1
    except Exception as e:
        logger.fatal(f'Cannot create dir: {path}')
        return -1
    else:
        return 0


def download_package(package, dist_url, name):
    try:
        response = requests.get(dist_url)
    except Exception:
        logger.error(f'File: failed to download {name}')
        return -1
    else:
        try:
            with open(os.path.join(config['PACKAGE_ROOT'], package, name), 'wb+') as f:
                f.write(response.content)
        except Exception:
            logger.error(f'File: failed to save {name}.')
        else:
            logger.info(f'File: saved {package}/{name}')
        return 0


def download_package_dists(package):
    if make_dir(os.path.join(config['PACKAGE_ROOT'], package)) < 0:
        return -1

    exceptions = []
    url = '/'.join((config['PYPI_SRC'], package))
    try:
        package_dir_response = requests.get(url)
    except:
        logger.error(f'Package: failed to get list of {package}')
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
        logger.fatal(f'Failed to load requirement file {args.PIP_LIST}')
        sys.exit(-1)

    packages = tuple(map(get_package_name, packages))    
 
    if args.dir:
        config['PACKAGE_ROOT'] = os.path.abspath(args.dir)

    if make_dir(config['PACKAGE_ROOT']) < 0:
        sys.exit(-1)

    if args.index_url:
        if not args.index_url.endswith('/simple') and not args.index_url.endswith('/simple/'):
            logger.error(f'URL {args.index_url} has an incorrect route, using {config["PYPI_SRC"]}')
        else:
            config['PYPI_SRC'] = args.index_url

    if args.recursive:
        logger.info('Acquiring packages in dependency tree...')
        try:
            packages_ = RequirementParser(packages).get_requirements(packages)
            packages = packages_
            print(packages)
        except TypeError as te:
            logger.error(str(te))

    download_packages(packages)

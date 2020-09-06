from gevent.monkey import patch_all
patch_all()

from utils import config, get_package_name, logger, make_dir
from bs4 import BeautifulSoup
import requests
import gevent
from urllib.parse import urljoin
import time
import sys
import re
import random
import os
import json
import argparse
import itertools
from math import ceil
from gevent.queue import Queue
from version import Version


class RequirementParser(object):
    def __init__(self, initial_packages: list):
        super().__init__()

        if not isinstance(initial_packages, (list, tuple)):
            raise TypeError('Initial Packages should be a list or tuple')
        self.to_visit = set(initial_packages)
        self.visited = set()
        self.req_api_base = config['PYPI_JSON_API']

    def get_requirements(self):
        while self.to_visit:
            greenlets = [gevent.spawn(self._get_requirement, package)
                         for package in self.to_visit]
            self.visited.update(self.to_visit)
            self.to_visit.clear()
            gevent.joinall(greenlets)
        return self.visited

    def _get_requirement(self, package):
        try:
            response = requests.get(self.req_api_base.format(package))
            requirements = json.loads(response.content)[
                'info']['requires_dist']
        except:
            return None

        if requirements and isinstance(requirements, list):
            requirements = {i.replace(';', ' ').split()[
                0] for i in requirements}
            requirements = set(
                filter(lambda x: x not in self.visited, requirements))
            requirements = {i.replace('.', '-') for i in requirements}
            self.to_visit.update(requirements)
        return None


class PackageDownloader(object):
    def __init__(self, time_delay, maximum_downloads, latest_versions=None):
        self.time_delay = time_delay
        self.maximum_downloads = maximum_downloads
        self.max_per_package = int(120 / self.maximum_downloads)
        self.latest_versions = latest_versions

    def _random_sleep(self, ratio=1.0):
        if ratio == 0 or self.time_delay == 0:
            return
        time.sleep(random.random() * (self.time_delay * ratio))

    def download_package(self, package, dist_url, name):
        """
        Download a single package.
        """
        try:
            self._random_sleep()
        
            with gevent.Timeout(120, TimeoutError) as timeout:
                response = requests.get(dist_url)

        except Exception:
            logger.error(f'File: failed to download {name}')
            return -1
        else:
            if response.status_code != 200:
                return -1
            elif response.content.startswith(b'<html'):
                return -1
            try:
                with open(os.path.join(config['PACKAGE_ROOT'], package, name), 'wb+') as f:
                    f.write(response.content)
            except Exception:
                logger.error(f'File: failed to save {name}.')
                return -1
            else:
                logger.info(f'File: saved {package}/{name}')
            return 0

    def clip_versions(self, soup):
        packages = soup.findAll('a')

        if self.latest_versions > 0:
            versions, ver_list = set(), []
            for x in packages:
                search = re.search('\d+(\.\d+)+[-\.]', x.text)
                if search:
                    version = Version(search.group()[:-1])
                    versions.add(version)
                    ver_list.append(version)
                else:
                    ver_list.append(None)
            download_versions = sorted(versions)[-self.latest_versions:]
            packages = [i[0] for i in list(filter(lambda x: x[1] in download_versions, (x for x in zip(packages, ver_list))))]

        package_dists = tuple(map(lambda x: (urljoin(config['PYPI_SRC'], x.attrs['href']), x.text), packages))

        return package_dists

    def download_package_dists(self, package):
        """
        Downloads all redistributable versions of a package.
        Return 0 if no error occured in this method.
        Return -1 if creation of package directory failed or failed.
        """
        if make_dir(os.path.join(config['PACKAGE_ROOT'], package)) < 0:
            return -1

        self._random_sleep(0.5)
        finished, failed = 0, 0

        url = '/'.join((config['PYPI_SRC'], package))
        try:
            package_dir_response = requests.get(url)
        except:
            logger.error(f'Package: failed to get list of {package}')
            return -1
        else:
            if package_dir_response.status_code != 200:
                return -1

        soup = BeautifulSoup(package_dir_response.content, 'lxml')
        package_dists = self.clip_versions(soup)
        total = len(package_dists)

        print(f'[Downloading] {package:>20s}, total: {(total):4d}')
        
        jobs = [gevent.spawn(self.download_package, package, dist_url, name)
                for (dist_url, name) in package_dists]

        li = []
        batch = ceil(total / self.max_per_package)
        for i in range(batch):
            li.extend(gevent.joinall(jobs[i * self.max_per_package : (i + 1) * self.max_per_package]))

        failed = -sum([l.value for l in li])
        finished = total - failed
        # TODO: change output to be logger
        print(
            f'[Downloaded]  {package:>20s}, total: {(total):4d}, finished: {finished:4d}, failed: {failed:4d}')
        return 0

    def download_packages(self, packages):
        res = []
        batches = ceil(len(packages) / self.maximum_downloads)
        for i in range(batches):
            batch = packages[i * self.maximum_downloads: (i + 1) * self.maximum_downloads]

            # TODO: change output to be logger
            print(f'Downloading batch {i}: {batch}')

            jobs = [gevent.spawn(self.download_package_dists, package)
                    for package in batch]
            res.extend([g.value for g in gevent.joinall(jobs)])
        return res


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("PIP_LIST", default="requirement.txt",
                        help="the pip-freeze format file for packages to be included")
    parser.add_argument(
        '-d', '--dir', help="the directory for saving packages")
    parser.add_argument('-i', '--index-url',
                        help="optional url for acquiring packages from")
    parser.add_argument('-R', '--recursive', action="store_true",
                        help="download packages in dependency trees recursively")
    parser.add_argument('-w', '--working-packages', type=int, default=4,
                        help="the maximum package number to download simultaneously")
    parser.add_argument('-t', '--time-delay', type=float, default=2.0,
                        help="the maximum random time delay to download each package")
    parser.add_argument('-p', '--packages', type=str,
                        help="check packages appeared only in this argument, comma-separated string. if used, dumps output into `PIP_LIST`")
    parser.add_argument('-l', '--latest-versions', default=-1, type=int,
                        help="download only the latest N versions, if N is given by this option")
    args = parser.parse_args()

    if args.packages:
        packages = args.packages.split(',')
    else:
        try:
            with open(args.PIP_LIST, 'r+') as f:
                packages = f.readlines()
        except OSError:
            logger.fatal(f'Failed to load requirement file {args.PIP_LIST}')
            sys.exit(-1)

    packages = tuple(map(get_package_name, packages))

    if args.dir:
        config['PACKAGE_ROOT'] = os.path.abspath(args.dir)

    if make_dir(config['PACKAGE_ROOT']) < 0:
        sys.exit(-1)

    if args.index_url:
        if not re.match(r'http[s]?://(\w*\.)+(\w*)\/simple\/?', args.index_url):
            logger.error(
                f'URL {args.index_url} has an incorrect route, using {config["PYPI_SRC"]}')
        else:
            config['PYPI_SRC'] = args.index_url

    if args.recursive:
        logger.info('Acquiring packages in dependency tree...')
        try:
            packages_ = RequirementParser(packages).get_requirements()
            packages = packages_
            with open(args.PIP_LIST, 'w+') as f:
                f.write('\n'.join(packages))
        except TypeError as te:
            logger.error(str(te))
    else:
        downloader = PackageDownloader(args.time_delay, args.working_packages, args.latest_versions)
        downloader.download_packages(packages)

# HapPypi - Handily Acquiring Packages from Pypi

## Description
HapPypi(pronounced `Happy Pie`) is a set of scripts for syncing local pypi packages from a remote src using http protocol. 

Aimed to provide an on-go, flexible toolset, HapPypi is under construction and could be useful for downloading packages on occasions when packages are needed to be imported in an offline LAN.

## Requirements(Development Environment)
* Python: 3.6+
* Packages: 
  * `gevent`
  * `requests`
  * `bs4`
  * `lxml`(for parser in `bs4`)

## Usage
HapPypi uses `happy.py` as cli entry. Usages are listed below.

```
usage: happy.py [-h] [-d DIR] [-i INDEX_URL] [-R] [-w WORKING_PACKAGES]
                [-t TIME_DELAY] [-p PACKAGES] [-l LATEST_VERSIONS]
                PIP_LIST

positional arguments:
  PIP_LIST              the pip-freeze format file for packages to be included

optional arguments:
  -h, --help            show this help message and exit
  -d DIR, --dir DIR     the directory for saving packages
  -i INDEX_URL, --index-url INDEX_URL
                        optional url for acquiring packages from
  -R, --recursive       download packages in dependency trees recursively
  -w WORKING_PACKAGES, --working-packages WORKING_PACKAGES
                        the maximum package number to download simultaneously
  -t TIME_DELAY, --time-delay TIME_DELAY
                        the maximum random time delay to download each package
  -p PACKAGES, --packages PACKAGES
                        check packages appeared only in this argument, comma-
                        separated string. if used, dumps output into
                        `PIP_LIST`
  -l LATEST_VERSIONS, --latest-versions LATEST_VERSIONS
                        download only the latest N versions, if N is given by
                        this option

```

### NOTE
Currently, `happy` would only allow **ONE** file like `requirement.txt`. The versions(such as `==x.x.x`, `>=x.x.x`, etc.) in each line are automatically ignored.


## Features
* **partially downloads** limited versions of packages, given specified requirements.


## Future Features
* **visualization** from command line window / tkinter window.
    
    A global monitoring map(which user block to represent all versions of a package) would be generated in a specified window and updated regularly.

* **compress** downloaded files into a file(->zip / ->tar->gzip).
* generate a set of scripts which could be used for running **a small [pypiserver](https://pypi.org/project/pypiserver/)**.

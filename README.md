# HapPypi - Handily Acquiring Packages from Pypi

## Description
HapPypi(pronounced `Happy Pie`) is a set of scripts for syncing local pypi packages from a remote src using http protocol. 

Aimed to provide an on-go, flexible toolset, HapPypi is under construction and could be useful for downloading packages on occasions when packages are needed to be imported in an offline LAN.

## Requirements(Development Environment)
* Python: 3.6+
* Packages: 
  * `pip`
  * `gevent`
  * `requests`
  * `bs4`

## Usage
HapPypi uses `happy.py` as cli entry. Usages are listed below.

```
usage: happy.py [-h] [-d DIR] PIP_LIST

positional arguments:
  PIP_LIST           the pip-freeze format file for packages to be included

optional arguments:
  -h, --help         show this help message and exit
  -d DIR, --dir DIR  the directory for saving packages
```

### NOTE
Currently, `happy` would only allow **ONE** file like `requirement.txt`. The versions(such as `==x.x.x`, `>=x.x.x`, etc.) in each line are automatically ignored.

## Future Features
* **partially downloads** limited versions of packages, given specified requirements.
* **visualization** from command line window / tkinter window.
    
    A global monitoring map(which user block to represent all versions of a package) would be generated in a specified window and updated regularly.

* **compress** downloaded files into a file(->zip / ->tar->gzip).
* generate a set of scripts which could be used for running **a small [pypiserver](https://pypi.org/project/pypiserver/)**.
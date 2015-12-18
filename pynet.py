#!/usr/bin/env python

import os
import re
import sys
import gzip
import json
import pprint
import urllib
import urllib2
import hashlib
import tarfile
import shutil
import StringIO

PYNET_PATH = os.path.expanduser('~/.pynet')
VIRTUALENV_PATH = 'virtualenv'

class TarGzPackageNotFoundError(Exception):
    pass

class Md5MismatchError(Exception):
    pass

def splitext(path):
    for ext in ('.tar.gz', '.tar.bz2'):
        if path.endswith(ext):
            return path[:-len(ext)], path[-len(ext):]
    return os.path.splitext(path)

def checksum(filename):
    h = hashlib.md5()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            h.update(chunk)
    return h.hexdigest()

def latest_virtualenv():
    url = 'https://pypi.python.org/pypi/virtualenv/json'
    response = urllib2.urlopen(url)
    listing = json.load(response)
    for package in listing[sorted(listing.keys())[-1]]:
        if package['filename'].endswith('tar.gz'):
            return package
    raise TarGzPackageNotFoundError

def setup_virtualenv(path=os.path.join(PYNET_PATH, VIRTUALENV_PATH)):
    package = latest_virtualenv()
    tempfile = urllib.urlretrieve(package['url'], filename=None)[0]
    md5_digest = checksum(tempfile)
    if checksum(tempfile) != package['md5_digest']:
        raise Md5DigestMismatchError
    tar = tarfile.open(tempfile)
    tar.extractall(PYNET_PATH)
    os.remove(tempfile)
    return splitext(package['filename'])[0]

def main():
    print 'pynet.py:'
    print sys.argv
    version = setup_virtualenv()
    print version

if __name__ == '__main__':
    main()

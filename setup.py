#!/usr/bin/env python
# coding=utf-8

import os
from glob import glob
import platform

if os.environ.get('USE_SETUPTOOLS'):
    from setuptools import setup
    setup  # workaround for pyflakes issue #13
    setup_kwargs = dict(zip_safe=0)
else:
    from distutils.core import setup
    setup_kwargs = dict()

base_dir = '/opt/domino/'

data_files = [ 
    (base_dir, ['README.md']),
    ('/var/log/domino', [])
]

distro = platform.dist()[0]
distro_major_version = platform.dist()[1].split('.')[0]

def pkgPath(root, path, rpath="/"):
    """
        Package up a path recursively
    """
    global data_files
    if not os.path.exists(path):
        return
    files = []
    for spath in os.listdir(path):
        subpath = os.path.join(path, spath)
        spath = os.path.join(rpath, spath)
        if os.path.isfile(subpath):
            files.append(subpath)

    data_files.append((root + rpath, files))
    for spath in os.listdir(path):
        subpath = os.path.join(path, spath)
        spath = os.path.join(rpath, spath)
        if os.path.isdir(subpath):
            pkgPath(root, subpath, spath)

data_files.append(('%s/bin' % base_dir,
                   glob('bin/*')))
data_files.append(('%s/classes' % base_dir,
                   glob('classes/*.py')))
pkgPath('%s/www' % base_dir, 'www')


# init scripts
if distro in ['centos', 'redhat']:
    data_files.append(('/etc/init.d', ['redhat/init/domino-api', 'redhat/init/domino-comm']))
if distro == 'Ubuntu':
    data_files.append(('/etc/init', ['debian/upstart/domino-api.conf', 'debian/upstart/domino-comm.conf']))

def get_version():
    f = open('%s/version.txt' % os.path.dirname(os.path.realpath(__file__)))
    version = ''.join(f.readlines()).rstrip()
    f.close()
    return version

setup(
    name='domino',
    version=get_version(),
    url='https://github.com/CBarraford/domino',
    author='Chad Barraford',
    author_email='cbarraford@gmail.com',
    description='Domino is a monitoring frontend and alerting infrastructure',
    data_files=data_files,
)

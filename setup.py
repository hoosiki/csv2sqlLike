#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup


with open('README.md') as readme_file:
    readme = readme_file.read()

install_requireent = []

setup_requires = [
        'pymysql',
        'pandas',
        'tqdm',
        'sqlalchemy',
        'mysql-connector-python'
        ]

install_requires = [
        'pymysql',
        'pandas',
        'tqdm',
        'sqlalchemy',
        'mysql-connector-python'
        ]

setup(
    name='csv2sqllike',
    author='Junsang Park',
    author_email='publichey@gmail.com',
    url='https://github.com/hoosiki/csv2sqlLike',
    version='1.2.7',
    long_description=readme,
    long_description_content_type="text/markdown",
    description='Python functions for data analysis using python native container. Load data from csv files and deal with data like sql.',
    packages=find_packages(),
    license='BSD',
    include_package_date=False,
    setup_requires=setup_requires,
    install_requires=install_requires,
    download_url='https://github.com/hoosiki/csv2sqlLike/blob/master/dist/csv2sqllike-1.2.7.tar.gz'
)

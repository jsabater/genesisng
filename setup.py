# -*- coding: utf-8 -*-
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='genesisng',
      version='0.2',
      description='Example package on how to use SQLAlchemy within Zato',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/jsabater/genesisng',
      author='Jaume Sabater',
      author_email='jsabater@gmail.com',
      license='MIT',
      keywords='sqlalchemy zato api services',
      packages=setuptools.find_packages(),
      classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
      ],
      install_requires=[
        'bcrypt',
        'configparser',
        'hashids',
        'httplib2',
        'nanoid',
        'passlib',
        'psycopg2',
        'psycopg2-binary',
        'sphinx',
        'sphinx_rtd_theme',
        'sqlalchemy'
      ],
      include_package_data=True,
      zip_safe=False)

# -*- coding: utf-8 -*-
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from setuptools import setup, find_packages
from io import open

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='genesisng',
      version='0.3',
      author='Jaume Sabater',
      author_email='jsabater@gmail.com',
      description='Example package on how to use SQLAlchemy within Zato',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/jsabater/genesisng',
      license='MIT',
      keywords=['sqlalchemy', 'zato', 'api', 'services'],
      packages=find_packages(where='src'),
      package_dir={"": "src"},
      classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
         "Operating System :: OS Independent",
         "Intended Audience :: Developers",
         "Development Status :: 5 - Production/Stable",
         "Natural Language :: English",
      ],
      install_requires=[
        'bcrypt',
        'configparser',
        'dictalchemy',
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
      python_requires='>=3.6',
      include_package_data=True,
      zip_safe=False)

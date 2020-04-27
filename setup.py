# -*- coding: utf-8 -*-
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from setuptools import setup, find_packages
from io import open


# Get long description from README.md file
with open("README.md", "r") as fh:
    long_description = fh.read()

# Get version and author from the package __init__ file
with open("src/genesisng/__init__.py", "r") as fh:
    for line in fh:
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            version = line.split(delim)[1]
        elif line.startswith('__author__'):
            delim = '"' if '"' in line else "'"
            author = line.split(delim)[1]
        elif line.startswith('__author_email__'):
            delim = '"' if '"' in line else "'"
            author_email = line.split(delim)[1]

setup(name='genesisng',
      version=version,
      author=author,
      author_email=author_email,
      description='Example package on how to use SQLAlchemy within Zato',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/jsabater/genesisng',
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
          'bunch',
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

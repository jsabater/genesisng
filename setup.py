# -*- coding: utf-8 -*-
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
from setuptools import setup

setup(name='genesisng',
      version='0.1',
      description='Genesis Next Generation',
      long_description='Example package on how to use SQLAlchemy with Zato',
      url='https://bitbucket.org/jsabater/genesisng',
      author='Jaume Sabater',
      author_email='jsabater@gmail.com',
      license='MIT',
      keywords='sqlalchemy zato api services',
      packages=['genesisng'],
      install_requires=[
        'configparser',
        'hashids',
        'psycopg2',
        'sqlalchemy'
      ],
      include_package_data=True,
      zip_safe=False)

# -*- coding: utf-8 -*-

from setuptools import setup

setup(name='genesisng',
      version='0.1',
      description='Example package on how to use SQLAlchemy with Zato',
      url='https://bitbucket.org/jsabater/genesisng',
      author='Jaume Sabater',
      author_email='jsabater@gmail.com',
      license='MIT',
      packages=['genesisng'],
      install_requires=['configparser', 'psycopg2', 'sqlalchemy']
      zip_safe=False)


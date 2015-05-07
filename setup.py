#!/usr/bin/env python

from setuptools import setup, find_packages
import versioneer
versioneer.VCS = 'git'
versioneer.versionfile_source = 'testing/_version.py'
versioneer.versionfile_build = 'testing/_version.py'
versioneer.tag_prefix = ''  # tags are like 1.2.0
versioneer.parentdir_prefix = 'testing-'  # dirname like 'myproject-1.2.0'

CONSOLE_SCRIPTS = ['testing=testing.testing:main']
LONG = """
Ethereum system-testing
"""

setup(name="testing",
      packages=find_packages("."),
      description='Ethereum system-testing',
      long_description=LONG,
      author="caktux",
      author_email="caktux@gmail.com",
      url='https://github.com/ethereum/system-testing/',
      install_requires=[
          "rpc",
          "argparse",
          "bitcoin",
          "boto",
          "docopt",
          "elasticsearch",
          "elasticsearch-dsl",
          "fabric",
          "futures",
          "progressbar",
          "pygraphviz",
          "pysha3",
          "pytest",
          "pyethereum",
          "python-jsonrpc",
          "matplotlib"
      ],
      entry_points=dict(console_scripts=CONSOLE_SCRIPTS),
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      classifiers=[
          "Development Status :: 2 - Pre-Alpha",
          "Environment :: Console",
          "License :: OSI Approved :: MIT License",
          "Operating System :: MacOS :: MacOS X",
          "Operating System :: POSIX :: Linux",
          "Programming Language :: Python :: 2.7",
      ])

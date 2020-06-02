import sqlite3
from distutils.version import LooseVersion
import os

from setuptools import setup

# Skip this check on readthedocs, that has an older sqlite3 version, but
# for generating documentation it doesn't matter.
if LooseVersion(
  sqlite3.sqlite_version
) < LooseVersion("3.24.0") and not os.environ.get('READTHEDOCS'):
  raise ValueError(
    f"sqlite.sqlite_version={sqlite3.sqlite_version}, >=3.24.0 required"
  )

setup(
  name='icubam',
  description='ICU Bed Availability Monitor',
  license='Apache',
  packages=['icubam'],
  zip_safe=False,
  python_requires=">=3.7",
  package_data={
    # If any package contains *.txt or *.rst files, include them:
    "": ["*.env"]
  }
)

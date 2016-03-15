# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
Upload to S3

Licence
```````
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
__author__ = "Ahmet Demir <me@ahmet2mir.eu>"

from setuptools import setup, find_packages

version = '0.0.7'

setup(
    name='us3',
    version=version,
    long_description=open('README.rst').read(),
    url='https://github.com/ahmet2mir/python-us3.git',
    author='Ahmet Demir',
    author_email='me@ahmet2mir.eu',
    description='US3 helps you to manage files on AWS S3 or S3 compatible API like Ceph or Cleversafe',
    license='License :: OSI Approved :: Apache Software License',
    keywords=['s3', 'command line', 'cli'],
    packages=find_packages(),
    package_data = {'': ['README.rst']},
    install_requires=open('requirements.txt').read().splitlines(),
    entry_points={
        'console_scripts': [
            'us3=us3.us3:main'
        ],
    }
)

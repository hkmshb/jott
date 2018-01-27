# note: when installing via pip include flag `--process-dependency-links`

import os
from setuptools import setup, find_packages


## meta data
__version__ = "0.0"
__author__  = "Abdul-Hakeem Shaibu"
__description__ = "jott"
__long_description__ = \
'''A simple desktop note taking editor.
'''


requires = [
]

tests_requires = [
    'pytest',
    'pytest-cov'
]

setup(
    name='jott',
    version=__version__,
    description=__description__,
    long_description=__long_description__,
    author=__author__,
    author_email='hkmshb@gmail.com',
    url='https://github.com/hkmshb/jott.git',
    keywords='note editor',
    zip_safe=False,
    packages=find_packages(),
    platforms='any',
    install_requires=requires,
    extras_require={
        'test': tests_requires
    },
    dependency_links=[
    ],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: End Users/Desktop',
        'Natural Language :: English',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6'
        'Topic :: Desktop Environment',
        'Topic :: Text Editors'
    ]
)

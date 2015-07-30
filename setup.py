# -*- coding:utf-8 -*-
#from ez_setup import use_setuptools
#use_setuptools()

from setuptools import setup, find_packages
import re

main_py = open('webtest/__init__.py').read()
metadata = dict(re.findall("__([A-Z]+)__ = '([^']+)'", main_py))
__VERSION__ = metadata['VERSION']

setup(
    name='webtest',
    version=__VERSION__,
    author='APSL · Bernardo Cabezas Serra',
    author_email='bcabezas@apsl.net',
    packages=find_packages(),
    license='GPL',
    description="APSL web testing tool",
    long_description=open('README.rst').read(),
    entry_points={
        'console_scripts': [
            'webtest = webtest.main:main',
            'check_web = webtest.nrpe:test',
        ],
    },
    install_requires=[
        'selenium',
        'click',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GPL License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ],
    include_package_data=True,
    zip_safe=False,
)

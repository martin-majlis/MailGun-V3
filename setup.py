import os
import re

from setuptools import setup, find_packages

def fix_doc(txt):
	return re.sub(r'\.\. PYPI-BEGIN([\r\n]|.)*?PYPI-END', '', txt, re.DOTALL)

with open('README.rst') as fileR:
    README = fix_doc(fileR.read())

with open('CHANGES.rst') as fileC:
    CHANGES = fix_doc(fileC.read())

requires = [
    'requests',
]

tests_require = []

setup(
    name='MailGunV3',
    version='0.2.4',
    description='Python wrapper for Mailgun REST API.',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        'Programming Language :: Python',
    ],
    author='Martin Majlis',
    author_email='martin@majlis.cz',
    license='MIT',
    url='https://github.com/martin-majlis/MailGunV3',
    download_url='https://github.com/martin-majlis/MailGunV3/archive/master.tar.gz',
    keywords='mailgun mail',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    extras_require={
        'testing': tests_require,
    },
    install_requires=requires,
    platforms='any',
)

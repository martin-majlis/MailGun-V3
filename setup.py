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
    version='0.2.6',
    description='Mailgun - Fluent API for v3',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Communications :: Email',
        'Topic :: Software Development :: Libraries :: Python Modules',
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

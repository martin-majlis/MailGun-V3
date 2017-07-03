import os

from setuptools import setup, find_packages

#here = os.path.abspath(os.path.dirname(__file__))
# with open(os.path.join(here, 'README.txt')) as f:
#    README = f.read()
# with open(os.path.join(here, 'CHANGES.txt')) as f:
#    CHANGES = f.read()

requires = [
    'requests',
]

tests_require = []

setup(
    name='MailGunV3',
    version='0.2.1',
    description='Python wrapper for Mailgun REST API.',
    #long_description=README + '\n\n' + CHANGES,
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

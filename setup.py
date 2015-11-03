

from distutils.core import setup
import os

setup(name='pmatic',
    version='0.1',
    description='A simple API to to the Homematic CCU2',
    long_description='pmatic is a python library to provide access to the Homematic CCU2. You ' \
                     'can execute pmatic directly on the CCU2 or another system having Python ' \
                     'installed. With pmatic you can write your own Python scripts to communicate ' \
                     'with your CCU2 devices.',
    author='Lars Michelsen',
    author_email='lm@larsmichelsen.com',
    url='https://github.com/LaMi-/pmatic',
    license='GPLv2',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Embedded Systems',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    packages=[
      'pmatic',
      'pmatic.api',
    ],
    data_files=[
        ('/usr/share/doc/pmatic', ['LICENSE', 'README.md']),
    ],
)

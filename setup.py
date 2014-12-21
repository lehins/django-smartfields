from setuptools import setup, find_packages
import smartfields
import os, sys

def read(fname):
    path = os.path.join(os.path.dirname(__file__), fname)
    if sys.version < '3':
        return open(path).read()
    return open(path, encoding="utf-8").read()


setup(
    name='django-smartfields',
    version=smartfields.get_version(),
    packages=find_packages(),
    description="Django Model Fields that are smart.",
    long_description='%s\n\n%s' % (read('README.rst'), read('CHANGELOG.rst')),
    author='Alexey Kuleshevich',
    author_email='lehins@yandex.ru',
    license='GNU GPL v2.0',
    url='https://github.com/lehins/python-wepay',
    platforms=["any"],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    keywords=[
        "django", "model fields", "declarative", "file cleanup", "file conversion"
    ],
    install_requires=['django']
)

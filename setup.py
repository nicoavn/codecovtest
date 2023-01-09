import pathlib

from setuptools import setup

cdir = pathlib.Path(__file__).parent
README = cdir.joinpath('readme.rst').read_text('utf-8')
CHANGELOG = cdir.joinpath('changelog.rst').read_text('utf-8')

VERSION_SRC = cdir.joinpath('ABC', 'version.py').read_text('utf-8')
version_globals = {}
exec(VERSION_SRC, version_globals)


setup(
    name='AABC',
    version=version_globals['VERSION'],
    description='<short description>',
    author='Alvin Duran',
    author_email='alvin.durang@level12.io',
    url='',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
    ],
    packages=['ABC'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # use this for libraries; or
        # use requirements folder/files for apps
    ],
    entry_points='''
        [console_scripts]
        ABC = ABC.cli:cli_entry
    ''',
)

from distutils.core import setup

version = '0.1.0dev'

setup(name = 'Parson',
      version = version,
      author = 'Darius Bacon',
      author_email = 'darius@wry.me',
      py_modules = ['parson'],
      url = 'https://github.com/darius/parson',
      description = "A fancier parsing package.", # XXX
      long_description = open('README.md').read(),
      license = 'GNU General Public License (GPL)',
      classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Topic :: Software Development :: Interpreters',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing',
        ],
      keywords = 'parse,parser,parsing,peg,packrat,regex,grammar',
      )

from os import getenv

if getenv('DEV'):
    version = '0.0.0-dev.1'
else:
    version = '1.1.4'

__version__ = version

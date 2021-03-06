#!/usr/bin/python3

from distutils.core import setup
#from setuptools import setup
from setuptools.command.install import install
import os

class command(install):
    def run(self):
        print('Running custom command:')
        os.system('python3 translate/package/createPackage.py')

        print('Coping execution file to /usr/bin')
        os.system('cp -v translate/package/tranen.py /usr/bin/tranen')
        os.system('cp -v translate/package/tranzh.py /usr/bin/tranzh')
        os.system('cp -v translate/package/tranpic.py /usr/bin/tranpic')
        install.run(self)


 
#files = ["translate/package/*"]
 
setup(
    name = "Google-translate",
    version = "1.0",
    description = "Free google translate",
    author = "poemdistance",
    author_email = "poemdistance@gmail.com",
    url = "",
    packages = ['translate/package'],
    cmdclass={'install':command}
)

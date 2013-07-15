#!/usr/bin/python3

"""
Install stawebg:

    python3 setup.py install

"""

import sys
from distutils.core import setup
import distutils.command.install_scripts
import shutil

# Exit, if python version is 2
if sys.version_info.major == 2:
    sys.exit(1)


# Remove .py from scripts
class my_install(distutils.command.install_scripts.install_scripts):
    def run(self):
        distutils.command.install_scripts.install_scripts.run(self)
        for script in self.get_outputs():
            if script.endswith(".py"):
                shutil.move(script, script[:-3])

# Setup
if __name__ == '__main__':
    setup(
        name="stawebg",
        version="0.1",
        license="MIT",
        description="Static website generator",
        author="Sven Hertle",
        author_email="sven.hertle@googlemail.com",
        packages=["stawebg"],
        scripts=["stawebg.py"],
        cmdclass={"install_scripts": my_install},
    )

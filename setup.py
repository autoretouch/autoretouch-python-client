import subprocess

from setuptools import setup, find_packages
from setuptools.command.install import install


class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        install.run(self)
        # PUT YOUR POST-INSTALL SCRIPT HERE or CALL A FUNCTION - TODO


setup(
    name='api_client',
    version='2.0.0',
    packages=find_packages(exclude=['tests', 'assets', 'tmp']),
    install_requires=[
        "requests", "Click"
    ],
    entry_points={
        'console_scripts': [
            'autoretouch = cli.commands:autoretouch_cli',
        ],
    },
    cmdclass={
        'install': PostInstallCommand
    },
)

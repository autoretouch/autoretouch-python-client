import os
from subprocess import run

from setuptools import setup, find_packages
from setuptools.command.install import install


class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        install.run(self)
        config_root = os.path.join(os.path.expanduser("~"), ".config", "autoretouch")
        os.makedirs(config_root, exist_ok=True)
        run(f"cp .autoretouch-complete.zsh {config_root}/".split())
        os.system(f"echo \""
                  f"\n\n# autoretouch auto-completion"
                  f"\n. ~/.config/autoretouch/.autoretouch-complete.zsh\n\n"
                  f"\" >> ~/.zshrc "
                  f"&& . ~/.zshrc")


setup(
    name='autoretouch_cli',
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
        'install': PostInstallCommand,
        "developp": PostInstallCommand
    },
)

import os
from subprocess import run

from setuptools import setup, find_packages
from setuptools.command.install import install


class PostInstallCommand(install):
    """Post-installation for installation mode."""

    def run(self):
        install.run(self)
        try:
            config_root = os.path.join(os.path.expanduser("~"), ".config", "autoretouch")
            os.makedirs(config_root, exist_ok=True)
            run(f"cp .autoretouch-complete.zsh {config_root}/".split())
            os.system(f"echo \""
                      f"\n\n# autoretouch auto-completion"
                      f"\n. ~/.config/autoretouch/.autoretouch-complete.zsh\n\n"
                      f"\" >> ~/.zshrc "
                      f"&& . ~/.zshrc")
        except Exception as e:
            print(f"failed to install autocompletion. Exception was: {str(e)}")


print("*******", os.getcwd())
cwd = os.path.abspath(os.path.dirname(__file__))
print("*******", cwd)
REQUIREMENTS = open(os.path.join(cwd, "requirements.txt"), "r").readlines()

setup(
    name='autoretouch',
    version='0.0.1',
    author=["Antoine Daurat <antoine@autoretouch.com>", "Oliver Allweyer <oliver@autoretouch.com>",
             "Till Lorentzen <till@autoretouch.com>"],
    description="cli and python package to communicate with the autoRetouch API",
    license="BSD Zero",
    packages=find_packages(exclude=['tests', 'assets', 'tmp']),
    install_requires=REQUIREMENTS,
    entry_points={
        'console_scripts': [
            'autoretouch = autoretouch.cli.commands:autoretouch_cli',
        ],
    },
    package_data={
        "": ["*.zsh", "*.txt"]
    },
    cmdclass={
        'install': PostInstallCommand,
        "developp": PostInstallCommand
    },
)

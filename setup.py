import os
from subprocess import run

from setuptools import setup, find_packages
from setuptools.command.install import install


class PostInstallCommand(install):
    """Post-installation for installation mode."""
    # TODO
    #  - autocomplete bash, fish, powershell
    #  - windows support
    #  - no logs, no exception in autocomplete mode
    def run(self):
        install.run(self)
        try:
            config_root = os.path.join(os.path.expanduser("~"), ".config", "autoretouch")
            os.makedirs(config_root, exist_ok=True)
            run(f"cp autoretouch/.autoretouch-complete.zsh {config_root}/".split())
            string_to_add = "\n\n# autoretouch auto-completion\n. ~/.config/autoretouch/.autoretouch-complete.zsh\n\n"
            if os.path.isfile("~/.zshrc"):
                with open("~/.zshrc", "r") as f:
                    has_been_added = string_to_add in f.read()
                if not has_been_added:
                    os.system(f"echo \"{string_to_add}\" >> ~/.zshrc")
        except Exception as e:
            print(f"failed to install autocompletion. Exception was: {str(e)}")


with open("README.md", "r") as f:
    README = f.read()

setup(
    name='autoretouch',
    version='0.0.1',
    author=[
        "Antoine Daurat <antoine@autoretouch.com>",
        "Oliver Allweyer <oliver@autoretouch.com>",
        "Till Lorentzen <till@autoretouch.com>"
    ],
    description="cli and python package to communicate with the autoRetouch API",
    long_description=README,
    long_description_content_type='text/markdown',
    license="BSD Zero",
    packages=find_packages(exclude=['test', 'assets', 'tmp']),
    install_requires=[
        "requests",
        "click==8.1.3",
        "click-log==0.4.0"
    ],
    extra_requires={
        "test": [
            "assertpy"
        ],
    },
    include_package_data=True,
    package_data={
        "autoretouch": [".autoretouch-complete.zsh"]
    },
    entry_points={
        'console_scripts': [
            'autoretouch = autoretouch.cli.commands:autoretouch_cli',
        ],
    },
    cmdclass={
        'install': PostInstallCommand,
        "develop": PostInstallCommand
    },
)

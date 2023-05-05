#!/bin/zsh
# make sure you install everything with
# `pip install --upgrade setuptools twine`

set -e

python setup.py clean
python setup.py sdist

echo "Releasing: $(ls dist/)"

twine upload dist/* -u $(cat secrets/pypi-user) -p $(cat secrets/pypi-password)
#!/bin/bash

## MacOS RESTRICTION NOTE:
# non system python installations cannot access the screen to display gui windows,
# only python binaries found on the framework path can do this. This script walks
# around this by executing the gui using a system binary which uses an external
# site-packages.

set -eu

if [ ! -f $FXPYTHON ]; then
  echo "FXPYTHON path is invalid. Jott requires a valid path to a system framework python" >&2
  exit 1
fi

echo "Locating virtualenv site-packages ..."
PYTHONPATH=`python -c 'import wx, os.path as p; print(p.dirname(p.dirname(wx.__file__)))'`
if [ $? != 0 ] || [ ! $PYTHONPATH ]; then
    echo "Virtualenv site-packages not located ..."
    exit 1
fi

echo "Running Jott ..."
echo ""
export PYTHONPATH
$FXPYTHON -S $@

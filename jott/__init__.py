__version__ = '0.1.0'


import sys
import logging
import os, os.path as osp



# location to file from which JOTT got executed from
JOTT_EXEC = osp.abspath(
    osp.join(sys.argv[0],
    sys.getfilesystemencoding()))

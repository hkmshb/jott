import sys
import shutil
import tempfile
import os, os.path as osp


HERE = osp.abspath(osp.dirname(__file__))
TMPDIR = osp.abspath(osp.join(HERE, 'tmp'))
DATADIR = osp.abspath(osp.join(HERE, 'data'))

REAL_TMPDIR = tempfile.gettempdir()


def _setup_environment():
    '''Method to be run once before test suite starts'''
    os.environ.update({
        'JOTT_TEST_ROOT': os.getcwd(),
        'TMP': TMPDIR,
        'REAL_TMP': REAL_TMPDIR,
        'XDG_DATA_HOME': os.path.join(TMPDIR, 'data_home'),
        'XDG_DATA_DIRS': os.path.join(TMPDIR, 'data_dir'),
        'XDG_CONFIG_HOME': os.path.join(TMPDIR, 'config_home'),
        'XDG_CONFIG_DIRS': os.path.join(TMPDIR, 'config_dir'),
        'XDG_CACHE_HOME': os.path.join(TMPDIR, 'cache_home')
    })

    if os.path.isdir(TMPDIR):
        shutil.rmtree(TMPDIR)
    os.makedirs(TMPDIR)


_setup_environment()

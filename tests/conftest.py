import os
import pytest



HERE = os.path.dirname(__file__)
FIXTURE_BASE = os.path.join(HERE, 'fixtures') 


@pytest.fixture(scope='module')
def jbpath():
    return os.path.join(FIXTURE_BASE, 'jottbook')


@pytest.fixture(scope='module')
def jb(jbpath):
    return None

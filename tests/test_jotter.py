import pytest
from jott.jotter import Path



class TestPath:
    '''Test Path object.
    '''

    def generator(self, name):
        return Path(name)

    def test_valid_page_name(self):
        # valid names
        for name in ('test', 'test this', 'test (this)', 'test:this (2)'):
            Path.assert_valid_page_name(name)

        # invalid names
        for name in (':test', '+test', 'foo:_bar', 'foo::bar', 'foo#bar'):
            assert pytest.raises(
                AssertionError,
                Path.assert_valid_page_name, name)

    def test_namespaced_page_names(self):
        for name, ns, basename in (
            ('Test:foo', 'Test', 'foo'),
            ('Test', '', 'Test')
        ):
            # test name
            Path.assert_valid_page_name(name)
            assert Path.make_valid_page_name(name) == name

            # get object
            path = self.generator(name)

            # test basic props
            assert path.name == name
            assert path.basename == basename
            assert path.namespace == ns
            assert path.name in path.__repr__()


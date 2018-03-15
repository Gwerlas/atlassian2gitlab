import pytest
from atlassian2gitlab.gl_resources import User
from atlassian2gitlab.exceptions import A2GException
from munch import munchify


def test_getattr_from_cached_object():
    user = User('name', None)
    user._item = munchify({'name': 'blah'})
    assert user.name == 'blah'


def test_user_not_found():
    manager = munchify({'gitlab': {'users': {
        'list': lambda username: []
    }}})
    user = User('name', manager)

    with pytest.raises(A2GException):
        user.get()


def test_get_user():
    manager = munchify({'gitlab': {'users': {
        'list': lambda username: ['blah']
    }}})
    user = User('name', manager)
    assert user.get() == 'blah'

import pytest
from atlassian2gitlab.gl_resources import User
from atlassian2gitlab.exceptions import A2GException
from munch import munchify


def fakeManager(mocker):
    mock = mocker.patch('atlassian2gitlab.managers.GitlabManager')
    mgr = mock.return_value
    mgr.gitlab = mocker.MagicMock()
    mgr.gitlab.users = mocker.MagicMock()
    return mgr


def test_getattr_from_cached_object():
    user = User('name')
    user._item = munchify({'name': 'blah'})
    assert user.name == 'blah'


def test_user_not_found(mocker):
    manager = fakeManager(mocker)
    manager.gitlab.users.list.return_value = []
    user = User('name')

    with pytest.raises(A2GException):
        user.get()


def test_get_user(mocker):
    manager = fakeManager(mocker)
    manager.gitlab.users.list.return_value = ['blah']
    user = User('name')
    assert user.get() == 'blah'

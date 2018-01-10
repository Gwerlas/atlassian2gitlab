import pytest
import requests
from atlassian2gitlab.gitlab import Gitlab


def test_getProjectId(mocker):
    gitlab = Gitlab('http://url/', 'user/project', 'my-token')
    r = mocker.stub()
    r.json = lambda: [{'id': 1, 'path_with_namespace': 'user/project'}]

    mocker.patch('requests.get', return_value=r)

    mocker.spy(gitlab, 'getProjectId')
    assert gitlab.getProjectId() == 1


def test_getProjectId_request_once(mocker):
    gitlab = Gitlab('http://url/', 'user/project', 'my-token')
    gitlab.projectId = 1

    mocker.patch('requests.get')

    mocker.spy(gitlab, 'getProjectId')
    assert gitlab.getProjectId() == 1
    requests.get.assert_not_called()


def test_projectId_raise_exception(mocker):
    gitlab = Gitlab('http://url/', 'user/project', 'my-token')
    r = mocker.stub()
    r.json = lambda: [{'id': 1, 'path_with_namespace': 'other/project'}]

    mocker.patch('requests.get', return_value=r)

    mocker.spy(gitlab, 'getProjectId')
    with pytest.raises(Exception):
        gitlab.getProjectId()


def test_addIssue(mocker):
    gitlab = Gitlab('http://url/', 'user/project', 'my-token')
    gitlab.projectId = 1
    mocker.patch('requests.post')

    gitlab.addIssue({})
    requests.post.assert_called_once_with(
        'http://url/api/v4/projects/1/issues',
        headers={'PRIVATE-TOKEN': 'my-token'},
        data={})

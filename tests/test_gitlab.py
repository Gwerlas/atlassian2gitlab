import pytest
from atlassian2gitlab.gitlab import Gitlab


def test_raise_exception_if_project_not_found(mocker):
    gitlab = mocker.patch('atlassian2gitlab.gitlab.Gitlab')

    with pytest.raises(Exception):
        Gitlab.search_project_from_repo(gitlab, 'not/exists')

import atlassian2gitlab as a2g


def test_gitlab_client():
    assert a2g.clients.Gitlab().api_version == '4'


def test_jira_client(mocker):
    mock = mocker.patch('jira.JIRA')
    a2g.clients.Jira().blah
    assert mock.call_count == 1

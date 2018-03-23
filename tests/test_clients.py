import atlassian2gitlab as a2g
import logging


def test_gitlab_client():
    a2g.debug = True
    logger = logging.getLogger("requests.packages.urllib3")

    assert a2g.clients.Gitlab().api_version == '4'
    assert logger.getEffectiveLevel() == logging.DEBUG


def test_jira_client(mocker):
    mock = mocker.patch('jira.JIRA')

    a2g.clients.Jira().blah

    assert mock.call_count == 1

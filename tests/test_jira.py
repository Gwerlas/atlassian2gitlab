import requests
from atlassian2gitlab.jira import Jira


def test_get(mocker):
    mocker.patch('requests.get')

    jira = Jira('john.doe', 'secret', 'http://url/', 'KEY')
    jira.get('project=KEY')

    requests.get.assert_called_once_with(
        'http://url/rest/api/2/search?jql=project=KEY',
        auth=('john.doe', 'secret'),
        headers={'Content-Type': 'application/json'})


def test_getIssues(mocker):
    jira = Jira('john.doe', 'secret', 'http://url/', 'KEY')
    r = mocker.stub()
    r.json = lambda: {"issues": []}

    mocker.patch.object(jira, 'get', return_value=r)
    mocker.spy(jira, 'getIssues')

    assert jira.getIssues('project=KEY') == []


def test_getActiveIssues(mocker):
    jira = Jira('john.doe', 'secret', 'http://url/', 'KEY')
    mocker.patch.object(jira, 'getIssues')
    jira.getIssues.return_value = []

    assert jira.getActiveIssues() == []

    jira.getIssues.assert_called_once_with(
        'project=KEY+AND+(resolution=Unresolved+OR+Sprint+in+openSprints())' +
        '+ORDER+BY+createdDate+ASC&maxResults=10000')

import atlassian2gitlab as a2g
from atlassian2gitlab.managers import JiraManager, GitlabManager
from atlassian2gitlab.exceptions import A2GException
from munch import munchify
import logging


def test_instanciate_jira_client(mocker):
    manager = JiraManager()
    mock = mocker.patch('atlassian2gitlab.clients.Jira')
    manager.jira
    assert mock.call_count == 1


def test_no_jira_issues_to_copy(caplog, mocker):
    manager = JiraManager()
    manager._client = mocker.MagicMock()
    manager._client.fields.return_value = [
        {'name': 'Sprint', 'id': 'field1'},
        {'name': 'Story Points', 'id': 'field2'},
    ]
    manager._client.search_issues.return_value = []
    manager.cp()
    assert caplog.record_tuples == [
        ('atlassian2gitlab', logging.INFO, 'Nothing to do')
    ]


def test_copy_jira_issues_in_failure(caplog, mocker):
    manager = JiraManager()
    issue = munchify({
        'key': 'PRO-42',
        'fields': {'issuetype': {'name': 'Story'}}})
    manager._client = mocker.MagicMock()
    manager._client.fields.return_value = [
        {'name': 'Sprint', 'id': 'field1'},
        {'name': 'Story Points', 'id': 'field2'},
    ]
    manager._client.search_issues.return_value = [issue]
    project = mocker.patch('atlassian2gitlab.gl_resources.Project')
    project.addIssue.side_effect = A2GException('Fail !')
    GitlabManager()._project = project

    manager.cp()

    project.addIssue.assert_called_once_with(issue)
    assert caplog.record_tuples == [
        ('atlassian2gitlab', logging.INFO, '1 issues to migrate'),
        ('atlassian2gitlab', logging.WARNING, 'Skip issue PRO-42: Fail !'),
        ('atlassian2gitlab', logging.ERROR, 'Any issues migrated')
    ]


def test_copy_jira_issues_partially_in_failure(caplog, mocker):
    manager = JiraManager()
    issue_one = munchify({
        'key': 'PRO-42',
        'fields': {'issuetype': {'name': 'Story'}}})
    issue_two = munchify({
        'key': 'PRO-43',
        'fields': {'issuetype': {'name': 'Story'}}})
    issue_three = munchify({
        'key': 'PRO-44',
        'fields': {'issuetype': {'name': 'Documentation related'}}})
    manager._client = mocker.MagicMock()
    manager._client.fields.return_value = [
        {'name': 'Sprint', 'id': 'field1'},
        {'name': 'Story Points', 'id': 'field2'},
    ]
    manager._client.search_issues.return_value = [
        issue_one, issue_two, issue_three]
    project = mocker.patch('atlassian2gitlab.gl_resources.Project')
    project.addIssue.side_effect = [A2GException('Fail !'), None]
    GitlabManager()._project = project

    manager.cp()

    assert project.addIssue.call_count == 2
    assert caplog.record_tuples == [
        ('atlassian2gitlab', logging.INFO, '3 issues to migrate'),
        ('atlassian2gitlab', logging.WARNING, 'Skip issue PRO-42: Fail !'),
        ('atlassian2gitlab', logging.WARNING,
            "Skip issue PRO-44: It's an Epic"),
        ('atlassian2gitlab', logging.WARNING,
            '1/3 issues migrated (1 skipped)')
    ]


def test_copy_jira_issues(caplog, mocker):
    manager = JiraManager()
    issue = munchify({
        'key': 'PRO-42',
        'fields': {'issuetype': {'name': 'Story'}}})
    manager._client = mocker.MagicMock()
    manager._client.fields.return_value = [
        {'name': 'Sprint', 'id': 'field1'},
        {'name': 'Story Points', 'id': 'field2'},
    ]
    manager._client.search_issues.return_value = [issue]
    project = mocker.patch('atlassian2gitlab.gl_resources.Project')
    GitlabManager()._project = project

    manager.cp()

    project.addIssue.assert_called_once_with(issue)
    assert caplog.record_tuples == [
        ('atlassian2gitlab', logging.INFO, '1 issues to migrate'),
        ('atlassian2gitlab', logging.INFO, 'All done')
    ]

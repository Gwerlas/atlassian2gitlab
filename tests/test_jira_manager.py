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
    manager._jira = mocker.MagicMock()
    manager._jira.fields.return_value = [
        {'name': 'Sprint', 'id': 'field1'},
        {'name': 'Story Points', 'id': 'field2'},
    ]
    manager._jira.search_issues.return_value = []
    manager.cp()
    assert caplog.record_tuples == [
        ('atlassian2gitlab.managers', logging.INFO, 'Nothing to do')
    ]


def test_copy_jira_issues_in_failure(caplog, mocker):
    manager = JiraManager()
    issue = munchify({'key': 'PRO-42', 'fields': {}})
    manager._jira = mocker.MagicMock()
    manager._jira.fields.return_value = [
        {'name': 'Sprint', 'id': 'field1'},
        {'name': 'Story Points', 'id': 'field2'},
    ]
    manager._jira.search_issues.return_value = [issue]
    project = mocker.patch('atlassian2gitlab.gl_resources.Project')
    project.addIssue.side_effect = A2GException('Fail !')
    GitlabManager()._project = project

    manager.cp()

    project.addIssue.assert_called_once_with(issue)
    assert caplog.record_tuples == [
        ('atlassian2gitlab.managers', logging.WARNING,
            'Skip issue PRO-42: Fail !'),
        ('atlassian2gitlab.managers', logging.ERROR, 'Any issues migrated')
    ]


def test_copy_jira_issues_partially_in_failure(caplog, mocker):
    manager = JiraManager()
    issue_one = munchify({'key': 'PRO-42', 'fields': {}})
    issue_two = munchify({'key': 'PRO-43', 'fields': {}})
    manager._jira = mocker.MagicMock()
    manager._jira.fields.return_value = [
        {'name': 'Sprint', 'id': 'field1'},
        {'name': 'Story Points', 'id': 'field2'},
    ]
    manager._jira.search_issues.return_value = [issue_one, issue_two]
    project = mocker.patch('atlassian2gitlab.gl_resources.Project')
    project.addIssue.side_effect = [A2GException('Fail !'), None]
    GitlabManager()._project = project

    manager.cp()

    assert project.addIssue.call_count == 2
    assert caplog.record_tuples == [
        ('atlassian2gitlab.managers', logging.WARNING,
            'Skip issue PRO-42: Fail !'),
        ('atlassian2gitlab.managers', logging.WARNING, '1/2 issues migrated')
    ]


def test_copy_jira_issues(caplog, mocker):
    manager = JiraManager()
    issue = munchify({'key': 'PRO-42', 'fields': {}})
    manager._jira = mocker.MagicMock()
    manager._jira.fields.return_value = [
        {'name': 'Sprint', 'id': 'field1'},
        {'name': 'Story Points', 'id': 'field2'},
    ]
    manager._jira.search_issues.return_value = [issue]
    project = mocker.patch('atlassian2gitlab.gl_resources.Project')
    GitlabManager()._project = project

    manager.cp()

    project.addIssue.assert_called_once_with(issue)
    assert caplog.record_tuples == [
        ('atlassian2gitlab.managers', logging.INFO, 'All 1 issues migrated')
    ]

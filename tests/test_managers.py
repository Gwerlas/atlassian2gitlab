import atlassian2gitlab as a2g
from atlassian2gitlab.exceptions import A2GException
import logging
from munch import munchify


def test_gitlab_manager():
    manager = a2g.Manager()
    assert manager.gitlab.api_version == '4'


def test_gitlab_in_debug_mode():
    a2g.debug = True
    a2g.Manager().gitlab
    logger = logging.getLogger("requests.packages.urllib3")
    assert logging.getLogger().getEffectiveLevel() == logging.DEBUG
    assert logger.getEffectiveLevel() == logging.DEBUG


def test_project_manager():
    a2g.gitlab_repo = 'fake/project'
    manager = a2g.Manager()
    assert manager.project._name == 'fake/project'


def test_jira_manager(mocker):
    manager = a2g.JiraManager()
    mock = mocker.patch('jira.JIRA')
    manager.jira
    mock.assert_called_once()


def test_no_jira_issues_to_copy(caplog):
    manager = a2g.JiraManager()
    manager._jira = munchify({
        'search_issues': lambda jql: []
    })
    manager.cp()
    assert caplog.record_tuples == [
        ('atlassian2gitlab', logging.INFO, 'Nothing to do')
    ]


def test_copy_jira_issues_in_failure(caplog, mocker):
    manager = a2g.JiraManager()
    issue = munchify({'key': 'PRO-42', 'fields': {}})
    manager._jira = munchify({
        'search_issues': lambda jql: [issue]
    })
    manager._project = mocker.patch('atlassian2gitlab.gl_objects.Project')
    manager._project.addIssue.side_effect = A2GException('Fail !')

    manager.cp()

    manager._project.addIssue.assert_called_once_with({})
    assert caplog.record_tuples == [
        ('atlassian2gitlab', logging.WARNING, 'Skip issue PRO-42: Fail !'),
        ('atlassian2gitlab', logging.ERROR, 'Any issues migrated')
    ]


def test_copy_jira_issues_partially_in_failure(caplog, mocker):
    manager = a2g.JiraManager()
    issue_one = munchify({'key': 'PRO-42', 'fields': {}})
    issue_two = munchify({'key': 'PRO-43', 'fields': {}})
    manager._jira = munchify({
        'search_issues': lambda jql: [issue_one, issue_two]
    })
    manager._project = mocker.patch('atlassian2gitlab.gl_objects.Project')
    manager._project.addIssue.side_effect = [A2GException('Fail !'), None]

    manager.cp()

    assert manager._project.addIssue.call_count == 2
    assert caplog.record_tuples == [
        ('atlassian2gitlab', logging.WARNING, 'Skip issue PRO-42: Fail !'),
        ('atlassian2gitlab', logging.WARNING, '1/2 issues migrated')
    ]


def test_copy_jira_issues(caplog, mocker):
    manager = a2g.JiraManager()
    issue = munchify({'key': 'PRO-42', 'fields': {}})
    manager._jira = munchify({
        'search_issues': lambda jql: [issue]
    })
    manager._project = mocker.patch('atlassian2gitlab.gl_objects.Project')

    manager.cp()

    manager._project.addIssue.assert_called_once_with({})
    assert caplog.record_tuples == [
        ('atlassian2gitlab', logging.INFO, 'All 1 issues migrated')
    ]

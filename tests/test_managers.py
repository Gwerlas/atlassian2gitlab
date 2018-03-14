import atlassian2gitlab as a2g
from atlassian2gitlab.exceptions import A2GException
import logging
import pytest
from munch import munchify


def test_gitlab_manager():
    manager = a2g.Manager(None, None, None)
    assert manager.gitlab.api_version == '4'


def test_gitlab_in_debug_mode():
    a2g.debug = True
    a2g.Manager(None, None, None, debug=True).gitlab
    logger = logging.getLogger("requests.packages.urllib3")
    assert logging.getLogger().getEffectiveLevel() == logging.DEBUG
    assert logger.getEffectiveLevel() == logging.DEBUG


def test_project_manager():
    manager = a2g.Manager(None, None, 'fake/project')
    assert manager.project._name == 'fake/project'


def test_use_current_user_if_user_not_found(mocker):
    manager = a2g.Manager(None, None, None)
    gl = mocker.MagicMock()
    manager._gitlab = gl

    gl.users = mocker.MagicMock()
    gl.users.list.return_value = ['not', 'found']
    gl.user = mocker.MagicMock()
    gl.user.username = 'current'

    user = manager.findUser('user')
    assert user._name == 'current'
    assert gl.auth.call_count == 1


def test_find_user(mocker):
    manager = a2g.Manager(None, None, None)
    gl = mocker.MagicMock()
    manager._gitlab = gl

    gl.users = mocker.MagicMock()
    gl.users.list.return_value = ['me']

    user = manager.findUser('me')
    assert user._name == 'me'


def test_find_existing_milestone():
    project = munchify({
        'milestones': {
            'list': lambda search: [munchify({'title': search})]
        }
    })
    manager = a2g.Manager(None, None, None)
    manager._project = project

    assert manager.findMilestone('1.0').title == '1.0'


def test_find_milestone():
    project = munchify({
        'milestones': {'list': lambda search: []},
        'addMilestone': lambda version: munchify({'title': version})
    })
    manager = a2g.Manager(None, None, None)
    manager._project = project

    assert manager.findMilestone('2.0').title == '2.0'


def test_gitlab_upload(mocker):
    project = munchify({
        'upload': lambda filename, filedata: 'Gitlab attachment'
    })
    manager = a2g.Manager(None, None, None)
    manager._project = project
    attachment = mocker.MagicMock()
    attachment.id = '1'
    attachment.filename = 'blah.jpg'
    attachment.get.return_value = 'Data'

    assert manager.attachFile(attachment) == 'Gitlab attachment'
    assert attachment.get.call_count == 1


def test_jira_manager(mocker):
    manager = a2g.JiraManager(None, None, None, None, None, None, None)
    mock = mocker.patch('jira.JIRA')
    manager.jira
    mock.call_count == 1


def test_no_jira_issues_to_copy(caplog, mocker):
    manager = a2g.JiraManager(None, None, None, None, None, None, None)
    manager._jira = mocker.MagicMock()
    manager._jira.fields.return_value = [
        {'name': 'Sprint', 'id': 'field1'},
        {'name': 'Story Points', 'id': 'field2'},
    ]
    manager._jira.search_issues.return_value = []
    manager.cp()
    assert caplog.record_tuples == [
        ('atlassian2gitlab', logging.INFO, 'Nothing to do')
    ]


def test_copy_jira_issues_in_failure(caplog, mocker):
    manager = a2g.JiraManager(None, None, None, None, None, None, None)
    issue = munchify({'key': 'PRO-42', 'fields': {}})
    manager._jira = mocker.MagicMock()
    manager._jira.fields.return_value = [
        {'name': 'Sprint', 'id': 'field1'},
        {'name': 'Story Points', 'id': 'field2'},
    ]
    manager._jira.search_issues.return_value = [issue]
    manager._project = mocker.patch('atlassian2gitlab.gl_objects.Project')
    manager._project.addIssue.side_effect = A2GException('Fail !')

    manager.cp()

    manager._project.addIssue.assert_called_once_with(issue)
    assert caplog.record_tuples == [
        ('atlassian2gitlab', logging.WARNING, 'Skip issue PRO-42: Fail !'),
        ('atlassian2gitlab', logging.ERROR, 'Any issues migrated')
    ]


def test_copy_jira_issues_partially_in_failure(caplog, mocker):
    manager = a2g.JiraManager(None, None, None, None, None, None, None)
    issue_one = munchify({'key': 'PRO-42', 'fields': {}})
    issue_two = munchify({'key': 'PRO-43', 'fields': {}})
    manager._jira = mocker.MagicMock()
    manager._jira.fields.return_value = [
        {'name': 'Sprint', 'id': 'field1'},
        {'name': 'Story Points', 'id': 'field2'},
    ]
    manager._jira.search_issues.return_value = [issue_one, issue_two]
    manager._project = mocker.patch('atlassian2gitlab.gl_objects.Project')
    manager._project.addIssue.side_effect = [A2GException('Fail !'), None]

    manager.cp()

    assert manager._project.addIssue.call_count == 2
    assert caplog.record_tuples == [
        ('atlassian2gitlab', logging.WARNING, 'Skip issue PRO-42: Fail !'),
        ('atlassian2gitlab', logging.WARNING, '1/2 issues migrated')
    ]


def test_copy_jira_issues(caplog, mocker):
    manager = a2g.JiraManager(None, None, None, None, None, None, None)
    issue = munchify({'key': 'PRO-42', 'fields': {}})
    manager._jira = mocker.MagicMock()
    manager._jira.fields.return_value = [
        {'name': 'Sprint', 'id': 'field1'},
        {'name': 'Story Points', 'id': 'field2'},
    ]
    manager._jira.search_issues.return_value = [issue]
    manager._project = mocker.patch('atlassian2gitlab.gl_objects.Project')

    manager.cp()

    manager._project.addIssue.assert_called_once_with(issue)
    assert caplog.record_tuples == [
        ('atlassian2gitlab', logging.INFO, 'All 1 issues migrated')
    ]


def test_get_last_sprint_when_issue_has_none():
    manager = a2g.JiraManager(None, None, None, None, None, None, None)
    manager._jira = munchify({
        'fields': lambda: [{'name': 'Sprint', 'id': 'customfield_1'}],
    })
    issue_fields = munchify({'customfield_1': []})

    assert manager.getIssueLastSprint(issue_fields) is None


def test_get_last_isue_sprint():
    manager = a2g.JiraManager(None, None, None, None, None, None, None)
    manager._jira = munchify({
        'fields': lambda: [{'name': 'Sprint', 'id': 'customfield_1'}],
        'sprint': lambda id: id
    })
    issue_fields = munchify({'customfield_1': [
        'greenhopper.service.sprint.Sprint@51bf9a8d[id=78,rapidViewId=13',
        'greenhopper.service.sprint.Sprint@51bf8d9a[id=79,rapidViewId=13',
    ]})

    assert manager.getIssueLastSprint(issue_fields) == '79'

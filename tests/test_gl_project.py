import pytest
import logging
from munch import munchify
from atlassian2gitlab.gl_resources import Project
from atlassian2gitlab.exceptions import A2GException


def fakeManager(mocker):
    mock = mocker.patch('atlassian2gitlab.managers.GitlabManager')
    mgr = mock.return_value
    mgr.gitlab = mocker.MagicMock()
    mgr.gitlab.projects = mocker.MagicMock()
    return mgr


def test_create_project_raise_exception():
    project = Project(None)
    with pytest.raises(NotImplementedError):
        project.create()


def test_raise_exception_if_project_not_found(mocker):
    manager = fakeManager(mocker)
    manager.gitlab.projects.list.return_value = []
    project = Project('fake/name')

    with pytest.raises(A2GException):
        project.get()


def test_raise_exception_if_other_projects_found(mocker):
    manager = fakeManager(mocker)
    manager.gitlab.projects.list.return_value = munchify(
        [{'path_with_namespace': 'fake/project'}])
    project = Project('fake/name')

    with pytest.raises(A2GException):
        project.get()


def test_return_cached_project():
    project = Project('fake/name')
    fake = munchify({'path_with_namespace': 'fake/project'})
    project._item = fake

    assert project.get() == fake


def test_get_project(mocker):
    manager = fakeManager(mocker)
    manager.gitlab.projects.list.return_value = [
        munchify({'path_with_namespace': 'fake/project'})]
    project = Project('fake/project')

    assert project.get().path_with_namespace == 'fake/project'


def test_add_jira_issue(mocker):
    project = Project(None)
    mock = mocker.patch('atlassian2gitlab.gl_resources.Issue')
    issue = mock.return_value
    jira_issue = object()

    project.addIssue(jira_issue)

    issue.fillFromJira.assert_called_once_with(jira_issue)


def test_nothing_to_flush(caplog, mocker):
    logging.getLogger('atlassian2gitlab').setLevel(logging.INFO)
    project = Project('fake/project')
    project._item = munchify({
        'issues': {
            'list': lambda all: []
        },
        'milestones': {
            'list': lambda all: []
        }})
    project.flush()
    assert caplog.record_tuples == [
        ('atlassian2gitlab', logging.INFO, 'Nothing to do')
    ]


def test_flush_issues_in_complete_failure(mocker, caplog):
    project = Project('fake/project')
    issue = munchify({'id': 1})
    issue.delete = mocker.stub(name="issue")
    issue.delete.side_effect = Exception('Fail !')
    project._item = munchify({
        'issues': {
            'list': lambda all: [issue]
        },
        'milestones': {
            'list': lambda all: []
        }
    })
    project.flush()
    assert issue.delete.call_count == 1
    assert caplog.record_tuples == [
        ('atlassian2gitlab', logging.WARNING,
            'Issue 1 has not been deleted: Fail !'),
        ('atlassian2gitlab', logging.ERROR, 'Any issues deleted')
    ]


def test_flush_issues_with_failure(mocker, caplog):
    project = Project('fake/project')
    issue_one = munchify({'id': 1})
    issue_one.delete = mocker.stub(name="issue_one")
    issue_one.delete.side_effect = Exception('Fail !')
    issue_two = munchify({'id': 2})
    issue_two.delete = mocker.stub(name="issue_two")
    project._item = munchify({
        'issues': {
            'list': lambda all: [issue_one, issue_two]
        },
        'milestones': {
            'list': lambda all: []
        }
    })
    project.flush()
    assert issue_one.delete.call_count == 1
    assert issue_two.delete.call_count == 1
    assert caplog.record_tuples == [
        ('atlassian2gitlab', logging.WARNING,
            'Issue 1 has not been deleted: Fail !'),
        ('atlassian2gitlab', logging.WARNING, '1/2 issues deleted')
    ]


def test_flush_milestones_in_complete_failure(mocker, caplog):
    project = Project('fake/project')
    milestone = munchify({'title': 'Sprint 1'})
    milestone.delete = mocker.stub(name="issue")
    milestone.delete.side_effect = Exception('Fail !')
    project._item = munchify({
        'issues': {
            'list': lambda all: []
        },
        'milestones': {
            'list': lambda all: [milestone]
        }
    })
    project.flush()
    assert milestone.delete.call_count == 1
    assert caplog.record_tuples == [
        ('atlassian2gitlab', logging.WARNING,
            'Milestone "Sprint 1" has not been deleted: Fail !'),
        ('atlassian2gitlab', logging.ERROR, 'Any milestones deleted')
    ]


def test_flush_milestones_with_failure(mocker, caplog):
    project = Project('fake/project')
    milestone_one = munchify({'title': 'Sprint 1'})
    milestone_one.delete = mocker.stub(name="milestone_one")
    milestone_one.delete.side_effect = Exception('Fail !')
    milestone_two = munchify({'title': 'Sprint 2'})
    milestone_two.delete = mocker.stub(name="milestone_two")
    project._item = munchify({
        'issues': {
            'list': lambda all: []
        },
        'milestones': {
            'list': lambda all: [milestone_one, milestone_two]
        }
    })
    project.flush()
    assert milestone_one.delete.call_count == 1
    assert milestone_two.delete.call_count == 1
    assert caplog.record_tuples == [
        ('atlassian2gitlab', logging.WARNING,
            'Milestone "Sprint 1" has not been deleted: Fail !'),
        ('atlassian2gitlab', logging.WARNING, '1/2 milestones deleted')
    ]


def test_flush(mocker, caplog):
    project = Project('fake/project')
    issue = munchify({'id': 1})
    issue.delete = mocker.stub(name="issue")
    milestone = munchify({'title': 'Sprint 1'})
    milestone.delete = mocker.stub(name="milestone")
    project._item = munchify({
        'issues': {
            'list': lambda all: [issue]
        },
        'milestones': {
            'list': lambda all: [milestone]
        }
    })
    project.flush()
    assert issue.delete.call_count == 1
    assert caplog.record_tuples == [
        ('atlassian2gitlab', logging.INFO, 'All 1 issues deleted'),
        ('atlassian2gitlab', logging.INFO, 'All 1 milestones deleted')
    ]

import pytest
import logging
from munch import munchify
from atlassian2gitlab.gl_objects import Project
from atlassian2gitlab.exceptions import A2GException


def test_raise_exception_if_project_not_found():
    import platform
    print('Version: {}'.format(platform.version()))
    manager = munchify({'gitlab': {
        'projects': {
            'list': lambda search=None: []
        }
    }})
    project = Project('fake/name', manager)

    with pytest.raises(A2GException):
        project.get()


def test_raise_exception_if_other_projects_found():
    manager = munchify({'gitlab': {
        'projects': {
            'list': lambda search=None: munchify([{'path_with_namespace':
                                                   'fake/project'}])
        }
    }})
    project = Project('fake/name', manager)

    with pytest.raises(A2GException):
        project.get()


def test_return_cached_project():
    project = Project('fake/name', None)
    fake = munchify({'path_with_namespace': 'fake/project'})
    project._item = fake

    assert project.get() == fake


def test_get_project():
    manager = munchify({'gitlab': {'projects': {
        'list': lambda search=None: munchify([{'path_with_namespace':
                                             'fake/project'}])
    }}})
    project = Project('fake/project', manager)

    assert project.get().path_with_namespace == 'fake/project'


def test_add_jira_issue():
    fields = munchify({
        'created': 'now',
        'summary': 'My title',
        'assignee': {'name': 'john.doe'},
        'description': 'My description',
        'fixVersions': [{}]
    })
    manager = munchify({
        'findUser': lambda name: munchify({'id': 1}),
        'notation': lambda desc: munchify({'toMarkdown': lambda: desc}),
        'findMilestone': lambda version: munchify({'id': 1})
    })
    project = Project('fake/project', manager)
    project._item = munchify({
        'issues': {
            'create': lambda data: data
        }
    })

    assert project.addIssue(fields) == {
        'created_at': 'now',
        'title': 'My title',
        'assignee_ids': [1],
        'description': 'My description',
        'milestone_id': 1
    }


def test_add_milestone():
    version = munchify({'released': True, 'releaseDate': '2008-04-12'})

    project = Project('fake/project', None)
    project._item = munchify({
        'milestones': {
            'create': lambda data: munchify({'due_date': 0, 'state_event': 0})
        }
    })

    given = project.addMilestone(version)
    assert given.due_date == '2008-04-12'
    assert given.state_event == 'close'


def test_nothing_to_flush(caplog):
    project = Project('fake/project', object())
    project._item = munchify({
        'issues': {
            'list': lambda all: []
        }
    })
    project.flush()
    assert caplog.record_tuples == [
        ('atlassian2gitlab.gl_objects', logging.INFO, 'Nothing to do')
    ]


def test_flush_in_complete_failure(mocker, caplog):
    project = Project('fake/project', object())
    issue = munchify({'id': 1})
    issue.delete = mocker.stub(name="issue")
    issue.delete.side_effect = Exception('Fail !')
    project._item = munchify({
        'issues': {
            'list': lambda all: [issue]
        }
    })
    project.flush()
    assert issue.delete.call_count == 1
    assert caplog.record_tuples == [
        ('atlassian2gitlab.gl_objects', logging.WARNING,
            'Issue 1 has not been deleted: Fail !'),
        ('atlassian2gitlab.gl_objects', logging.ERROR, 'Any issues deleted')
    ]


def test_flush_with_failure(mocker, caplog):
    project = Project('fake/project', object())
    issue_one = munchify({'id': 1})
    issue_one.delete = mocker.stub(name="issue_one")
    issue_one.delete.side_effect = Exception('Fail !')
    issue_two = munchify({'id': 2})
    issue_two.delete = mocker.stub(name="issue_two")
    project._item = munchify({
        'issues': {
            'list': lambda all: [issue_one, issue_two]
        }
    })
    project.flush()
    assert issue_one.delete.call_count == 1
    assert issue_two.delete.call_count == 1
    assert caplog.record_tuples == [
        ('atlassian2gitlab.gl_objects', logging.WARNING,
            'Issue 1 has not been deleted: Fail !'),
        ('atlassian2gitlab.gl_objects', logging.WARNING, '1/2 issues deleted')
    ]


def test_flush(mocker, caplog):
    project = Project('fake/project', object())
    issue = munchify({'id': 1})
    issue.delete = mocker.stub(name="issue")
    project._item = munchify({
        'issues': {
            'list': lambda all: [issue]
        }
    })
    project.flush()
    assert issue.delete.call_count == 1
    assert caplog.record_tuples == [
        ('atlassian2gitlab.gl_objects', logging.INFO, 'All 1 issues deleted')
    ]

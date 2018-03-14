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


def test_add_jira_issue(mocker):
    issue = munchify({'fields': {
        'created': 'now',
        'summary': 'My title',
        'reporter': {'name': 'john.doe'},
        'assignee': {'name': 'john.doe'},
        'description': 'My description',
        'fixVersions': [],
        'attachment': []
    }})
    manager = mocker.MagicMock()
    manager.findUser.return_value = munchify({'id': 1, 'username': 'jdoe'})
    manager.getIssueLastSprint.return_value = None
    manager.getFieldId.return_value = 'field1'
    project = Project('fake/project', manager)
    project._item = munchify({
        'issues': {
            'create': lambda data, sudo: data
        }
    })

    assert project.addIssue(issue) == {
        'created_at': 'now',
        'title': 'My title',
        'assignee_ids': [1],
        'description': 'My description'
    }


def test_add_jira_issue_with_version(mocker):
    issue = munchify({'fields': {
        'created': 'now',
        'summary': 'My title',
        'reporter': {'name': 'john.doe'},
        'assignee': {'name': 'john.doe'},
        'description': 'My description',
        'fixVersions': [{}],
        'attachment': []
    }})
    manager = mocker.MagicMock()
    manager.findUser.return_value = munchify({'id': 1, 'username': 'jdoe'})
    manager.findMilestone.return_value = munchify({'id': 1})
    manager.getIssueLastSprint.return_value = None
    manager.getFieldId.return_value = 'field1'
    project = Project('fake/project', manager)
    project._item = munchify({
        'issues': {
            'create': lambda data, sudo: data
        }
    })

    assert project.addIssue(issue) == {
        'created_at': 'now',
        'title': 'My title',
        'assignee_ids': [1],
        'description': 'My description',
        'milestone_id': 1
    }


def test_add_jira_issue_with_sprint(mocker):
    issue = munchify({'fields': {
        'created': 'now',
        'summary': 'My title',
        'reporter': {'name': 'john.doe'},
        'assignee': {'name': 'john.doe'},
        'description': 'My description',
        'fixVersions': [],
        'attachment': []
    }})
    manager = mocker.MagicMock()
    manager.findUser.return_value = munchify({'id': 1, 'username': 'jdoe'})
    manager.findMilestone.return_value = munchify({'id': 1})
    manager.getIssueLastSprint.return_value = 'Sprint 1'
    manager.getFieldId.return_value = 'field1'
    project = Project('fake/project', manager)
    project._item = munchify({
        'issues': {
            'create': lambda data, sudo: data
        }
    })

    assert project.addIssue(issue) == {
        'created_at': 'now',
        'title': 'My title',
        'assignee_ids': [1],
        'description': 'My description',
        'milestone_id': 1
    }


def test_add_jira_issue_with_both_version_and_sprint(mocker):
    issue = munchify({'fields': {
        'created': 'now',
        'summary': 'My title',
        'reporter': {'name': 'john.doe'},
        'assignee': {'name': 'john.doe'},
        'description': 'My description',
        'fixVersions': [{}],
        'attachment': []
    }})
    manager = mocker.MagicMock()
    manager.findUser.return_value = munchify({'id': 1, 'username': 'jdoe'})
    manager.findMilestone.return_value = munchify({'id': 1})
    manager.getIssueLastSprint.return_value = 'Sprint 1'
    manager.getFieldId.return_value = 'field1'
    project = Project('fake/project', manager)
    project._item = munchify({
        'issues': {
            'create': lambda data, sudo: data
        }
    })

    assert project.addIssue(issue) == {
        'created_at': 'now',
        'title': 'My title',
        'assignee_ids': [1],
        'description': 'My description',
        'milestone_id': 1
    }


def test_add_jira_issue_with_story_points(mocker):
    issue = munchify({'fields': {
        'created': 'now',
        'summary': 'My title',
        'reporter': {'name': 'john.doe'},
        'assignee': {'name': 'john.doe'},
        'description': 'My description',
        'fixVersions': [],
        'attachment': [],
        'field1': 10.0
    }})
    manager = mocker.MagicMock()
    manager.findUser.return_value = munchify({'id': 1, 'username': 'jdoe'})
    manager.getIssueLastSprint.return_value = None
    manager.getFieldId.return_value = 'field1'
    manager.getIssueWeight.return_value = 9
    project = Project('fake/project', manager)
    project._item = munchify({
        'issues': {
            'create': lambda data, sudo: data
        }
    })

    assert project.addIssue(issue) == {
        'created_at': 'now',
        'title': 'My title',
        'assignee_ids': [1],
        'description': 'My description',
        'weight': 9
    }
    manager.getIssueWeight.assert_called_once_with(10.0)


def test_add_milestone_from_sprint():
    sprint = munchify({'state': 'CLOSED', 'endDate': '2008-04-12'})

    project = Project('fake/project', None)
    project._item = munchify({
        'milestones': {
            'create': lambda data: munchify({
                'due_date': None,
                'state_event': None,
                'save': lambda: None
            })
        }
    })

    given = project.addMilestone(sprint)
    assert given.due_date == '2008-04-12'
    assert given.state_event == 'close'


def test_add_milestone_from_version():
    version = munchify({'released': True, 'releaseDate': '2008-04-12'})

    project = Project('fake/project', None)
    project._item = munchify({
        'milestones': {
            'create': lambda data: munchify({
                'due_date': None,
                'state_event': None,
                'save': lambda: None
            })
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
        },
        'milestones': {
            'list': lambda all: []
        }
    })
    project.flush()
    assert caplog.record_tuples == [
        ('atlassian2gitlab.gl_objects', logging.INFO, 'Nothing to do')
    ]


def test_flush_issues_in_complete_failure(mocker, caplog):
    project = Project('fake/project', object())
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
        ('atlassian2gitlab.gl_objects', logging.WARNING,
            'Issue 1 has not been deleted: Fail !'),
        ('atlassian2gitlab.gl_objects', logging.ERROR, 'Any issues deleted')
    ]


def test_flush_issues_with_failure(mocker, caplog):
    project = Project('fake/project', object())
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
        ('atlassian2gitlab.gl_objects', logging.WARNING,
            'Issue 1 has not been deleted: Fail !'),
        ('atlassian2gitlab.gl_objects', logging.WARNING, '1/2 issues deleted')
    ]


def test_flush_milestones_in_complete_failure(mocker, caplog):
    project = Project('fake/project', object())
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
        ('atlassian2gitlab.gl_objects', logging.WARNING,
            'Milestone "Sprint 1" has not been deleted: Fail !'),
        ('atlassian2gitlab.gl_objects', logging.ERROR,
            'Any milestones deleted')
    ]


def test_flush_milestones_with_failure(mocker, caplog):
    project = Project('fake/project', object())
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
        ('atlassian2gitlab.gl_objects', logging.WARNING,
            'Milestone "Sprint 1" has not been deleted: Fail !'),
        ('atlassian2gitlab.gl_objects', logging.WARNING,
            '1/2 milestones deleted')
    ]


def test_flush(mocker, caplog):
    project = Project('fake/project', object())
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
        ('atlassian2gitlab.gl_objects', logging.INFO, 'All 1 issues deleted'),
        ('atlassian2gitlab.gl_objects', logging.INFO,
            'All 1 milestones deleted')
    ]

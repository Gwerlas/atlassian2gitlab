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


def test_raise_exception_if_project_not_found(mocker):
    manager = fakeManager(mocker)
    manager.gitlab.projects.list.return_value = []

    with pytest.raises(A2GException):
        Project('fake/name')


def test_raise_exception_if_other_projects_found(mocker):
    manager = fakeManager(mocker)
    manager.gitlab.projects.list.return_value = munchify(
        [{'path_with_namespace': 'fake/project'}])

    with pytest.raises(A2GException):
        Project('fake/name')


def test_get_project(mocker):
    manager = fakeManager(mocker)
    manager.gitlab.projects.list.return_value = [
        munchify({'path_with_namespace': 'fake/project'})]
    project = Project('fake/project')

    assert project.path_with_namespace == 'fake/project'


def test_nothing_to_flush(caplog, mocker):
    logging.getLogger('atlassian2gitlab').setLevel(logging.INFO)
    manager = fakeManager(mocker)
    manager.gitlab.projects.list.return_value = [
        munchify({'path_with_namespace': 'fake/project'})]
    project = Project('fake/project')
    project._item = munchify({
        'branches': {'list': lambda all: []},
        'tags': {'list': lambda all: []},
        'issues': {'list': lambda all: []},
        'labels': {'list': lambda all: []},
        'milestones': {'list': lambda all: []},
    })
    project.flush()
    assert caplog.record_tuples == [
        ('atlassian2gitlab', logging.INFO, 'Nothing to do')
    ]


def test_flush_issues_in_complete_failure(mocker, caplog):
    manager = fakeManager(mocker)
    manager.gitlab.projects.list.return_value = [
        munchify({'path_with_namespace': 'fake/project'})]
    project = Project('fake/project')
    issue = munchify({'id': 1})
    issue.delete = mocker.stub(name="issue")
    issue.delete.side_effect = Exception('Fail !')
    project._item = munchify({
        'branches': {'list': lambda all: []},
        'tags': {'list': lambda all: []},
        'issues': {'list': lambda all: [issue]},
        'labels': {'list': lambda all: []},
        'milestones': {'list': lambda all: []},
    })
    project.flush()
    assert issue.delete.call_count == 1
    assert caplog.record_tuples == [
        ('atlassian2gitlab', logging.INFO, '1 issues to be deleted'),
        ('atlassian2gitlab', logging.WARNING,
            "Issue `1' has not been deleted: Fail !"),
        ('atlassian2gitlab', logging.ERROR, 'Any issues deleted')
    ]


def test_flush_issues_with_failure(mocker, caplog):
    manager = fakeManager(mocker)
    manager.gitlab.projects.list.return_value = [
        munchify({'path_with_namespace': 'fake/project'})]
    project = Project('fake/project')
    issue_one = munchify({'id': 1})
    issue_one.delete = mocker.stub(name="issue_one")
    issue_one.delete.side_effect = Exception('Fail !')
    issue_two = munchify({'id': 2})
    issue_two.delete = mocker.stub(name="issue_two")
    project._item = munchify({
        'branches': {'list': lambda all: []},
        'tags': {'list': lambda all: []},
        'issues': {'list': lambda all: [issue_one, issue_two]},
        'labels': {'list': lambda all: []},
        'milestones': {'list': lambda all: []},
    })
    project.flush()
    assert issue_one.delete.call_count == 1
    assert issue_two.delete.call_count == 1
    assert caplog.record_tuples == [
        ('atlassian2gitlab', logging.INFO, '2 issues to be deleted'),
        ('atlassian2gitlab', logging.WARNING,
            "Issue `1' has not been deleted: Fail !"),
        ('atlassian2gitlab', logging.WARNING, '1/2 issues deleted')
    ]


def test_flush_milestones_in_complete_failure(mocker, caplog):
    manager = fakeManager(mocker)
    manager.gitlab.projects.list.return_value = [
        munchify({'path_with_namespace': 'fake/project'})]
    project = Project('fake/project')
    milestone = munchify({'title': 'Sprint 1'})
    milestone.delete = mocker.stub(name="milestone")
    milestone.delete.side_effect = Exception('Fail !')
    project._item = munchify({
        'branches': {'list': lambda all: []},
        'tags': {'list': lambda all: []},
        'issues': {'list': lambda all: []},
        'labels': {'list': lambda all: []},
        'milestones': {'list': lambda all: [milestone]}
    })
    project.flush()
    assert milestone.delete.call_count == 1
    assert caplog.record_tuples == [
        ('atlassian2gitlab', logging.INFO, '1 milestones to be deleted'),
        ('atlassian2gitlab', logging.WARNING,
            "Milestone `Sprint 1' has not been deleted: Fail !"),
        ('atlassian2gitlab', logging.ERROR, 'Any milestones deleted')
    ]


def test_flush_milestones_with_failure(mocker, caplog):
    manager = fakeManager(mocker)
    manager.gitlab.projects.list.return_value = [
        munchify({'path_with_namespace': 'fake/project'})]
    project = Project('fake/project')
    milestone_one = munchify({'title': 'Sprint 1'})
    milestone_one.delete = mocker.stub(name="milestone_one")
    milestone_one.delete.side_effect = Exception('Fail !')
    milestone_two = munchify({'title': 'Sprint 2'})
    milestone_two.delete = mocker.stub(name="milestone_two")
    project._item = munchify({
        'branches': {'list': lambda all: []},
        'tags': {'list': lambda all: []},
        'issues': {'list': lambda all: []},
        'labels': {'list': lambda all: []},
        'milestones': {'list': lambda all: [milestone_one, milestone_two]}
    })
    project.flush()
    assert milestone_one.delete.call_count == 1
    assert milestone_two.delete.call_count == 1
    assert caplog.record_tuples == [
        ('atlassian2gitlab', logging.INFO, '2 milestones to be deleted'),
        ('atlassian2gitlab', logging.WARNING,
            "Milestone `Sprint 1' has not been deleted: Fail !"),
        ('atlassian2gitlab', logging.WARNING, '1/2 milestones deleted')
    ]


def test_flush_labels_in_complete_failure(mocker, caplog):
    manager = fakeManager(mocker)
    manager.gitlab.projects.list.return_value = [
        munchify({'path_with_namespace': 'fake/project'})]
    project = Project('fake/project')
    label = munchify({'name': 'Story'})
    label.delete = mocker.stub(name="label")
    label.delete.side_effect = Exception('Fail !')
    project._item = munchify({
        'branches': {'list': lambda all: []},
        'tags': {'list': lambda all: []},
        'issues': {'list': lambda all: []},
        'labels': {'list': lambda all: [label]},
        'milestones': {'list': lambda all: []}
    })
    project.flush()
    assert label.delete.call_count == 1
    assert caplog.record_tuples == [
        ('atlassian2gitlab', logging.INFO, '1 labels to be deleted'),
        ('atlassian2gitlab', logging.WARNING,
            "Label `Story' has not been deleted: Fail !"),
        ('atlassian2gitlab', logging.ERROR, 'Any labels deleted')
    ]


def test_flush_labels_with_failure(mocker, caplog):
    manager = fakeManager(mocker)
    manager.gitlab.projects.list.return_value = [
        munchify({'path_with_namespace': 'fake/project'})]
    project = Project('fake/project')
    label_one = munchify({'name': 'Story'})
    label_one.delete = mocker.stub(name="label_one")
    label_one.delete.side_effect = Exception('Fail !')
    label_two = munchify({'name': 'In Progress'})
    label_two.delete = mocker.stub(name="label_two")
    project._item = munchify({
        'branches': {'list': lambda all: []},
        'tags': {'list': lambda all: []},
        'issues': {'list': lambda all: []},
        'labels': {'list': lambda all: [label_one, label_two]},
        'milestones': {'list': lambda all: []}
    })
    project.flush()
    assert label_one.delete.call_count == 1
    assert label_two.delete.call_count == 1
    assert caplog.record_tuples == [
        ('atlassian2gitlab', logging.INFO, '2 labels to be deleted'),
        ('atlassian2gitlab', logging.WARNING,
            "Label `Story' has not been deleted: Fail !"),
        ('atlassian2gitlab', logging.WARNING, '1/2 labels deleted')
    ]


def test_flush(mocker, caplog):
    manager = fakeManager(mocker)
    manager.gitlab.projects.list.return_value = [
        munchify({'path_with_namespace': 'fake/project'})]
    project = Project('fake/project')
    branch_dev = munchify({'name': 'develop'})
    branch_dev.delete = mocker.stub(name="branch_dev")
    branch_master = munchify({'name': 'master'})
    branch_master.delete = mocker.stub(name="branch_master")
    tag = munchify({'name': 'v1.0'})
    tag.delete = mocker.stub(name="tag")
    issue = munchify({'id': 1})
    issue.delete = mocker.stub(name="issue")
    label = munchify({'name': 'Story'})
    label.delete = mocker.stub(name="label")
    milestone = munchify({'title': 'Sprint 1'})
    milestone.delete = mocker.stub(name="milestone")
    project._item = munchify({
        'default_branch': 'master',
        'branches': {'list': lambda all: [branch_dev, branch_master]},
        'tags': {'list': lambda all: [tag]},
        'issues': {'list': lambda all: [issue]},
        'labels': {'list': lambda all: [label]},
        'milestones': {'list': lambda all: [milestone]}
    })
    project.flush()
    assert issue.delete.call_count == 1
    assert label.delete.call_count == 1
    assert milestone.delete.call_count == 1
    assert branch_dev.delete.call_count == 1
    assert branch_master.delete.call_count == 0
    assert tag.delete.call_count == 1
    assert caplog.record_tuples == [
        ('atlassian2gitlab', logging.INFO, '1 issues to be deleted'),
        ('atlassian2gitlab', logging.INFO, 'Done'),
        ('atlassian2gitlab', logging.INFO, '1 labels to be deleted'),
        ('atlassian2gitlab', logging.INFO, 'Done'),
        ('atlassian2gitlab', logging.INFO, '1 milestones to be deleted'),
        ('atlassian2gitlab', logging.INFO, 'Done'),
        ('atlassian2gitlab', logging.INFO, '1 tags to be deleted'),
        ('atlassian2gitlab', logging.INFO, 'Done'),
        ('atlassian2gitlab', logging.INFO, '2 branches to be deleted'),
        ('atlassian2gitlab', logging.WARNING,
            "Skip the default branch `master'"),
        ('atlassian2gitlab', logging.INFO, 'Done'),
    ]

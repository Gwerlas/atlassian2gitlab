import pytest
from munch import munchify
import atlassian2gitlab as a2g
from atlassian2gitlab.gl_resources import Issue, Label
from gitlab.exceptions import GitlabGetError


def fakeGitlabManager(mocker):
    mock = mocker.patch('atlassian2gitlab.managers.GitlabManager')
    mgr = mock.return_value
    mgr.project = mocker.MagicMock()
    mgr.project.issues = mocker.MagicMock()
    mgr.project.labels = mocker.MagicMock()
    mgr.findUser.return_value = fakeUser()
    return mgr


def fakeJiraManager(mocker):
    mock = mocker.patch('atlassian2gitlab.managers.JiraManager')
    mgr = mock.return_value
    mgr.jira = mocker.MagicMock()
    mgr.getFieldId.side_effect = ['customfield_10001', 'customfield_10002']
    return mgr


class fakeUser(object):
    def __init__(self, id=1, name='jdoe'):
        self.id = id
        self.username = name


class fakeJiraIssue(object):
    key = 'PRO-1'

    def __init__(self):
        self.fields = munchify({
            'created': '2008-04-12 21:00:00',
            'summary': 'Title',
            'reporter': {'name': 'jdoe'},
            'assignee': {'name': 'jdoe'},
            'description': 'Big content',
            'fixVersions': [],
            'customfield_10001': None,
            'customfield_10002': 5,
            'issuetype': {'name': 'Story', 'iconUrl': 'http://url'},
            'status': {
                'name': 'To Do',
                'iconUrl': 'httpr://url',
                'raw': {
                    'statusCategory': {'key': 'new', 'colorName': 'blue'}}},
            'resolution': None
        })

    def permalink(self):
        return 'http://url/'


def test_todo_issue_in_sprint(mocker):
    a2g.link_to_jira_source = False

    jira_manager = fakeJiraManager(mocker)
    jira_manager.jira.sprint.return_value = 'Sprint 1'

    jira_issue = fakeJiraIssue()
    jira_issue.fields.customfield_10001 = ['id=20,']

    gl_manager = fakeGitlabManager(mocker)
    gl_manager.project.labels.get.side_effect = GitlabGetError
    gl_label = Label('Story')
    gl_label.color = None
    gl_manager.findLabel.return_value = gl_label
    gl_milestone = mocker.MagicMock()
    gl_milestone.id = 1
    gl_manager.findMilestone.return_value = gl_milestone

    issue = Issue()
    mocker.patch.object(issue, 'getDominantColorFromUrl')
    issue.getDominantColorFromUrl.return_value = '#cccccc'

    issue.fillFromJira(jira_issue)

    gl_manager.project.issues.create.assert_called_once_with({
        'created_at': '2008-04-12T21:00:00',
        'title': 'Title',
        'assignee_ids': [1],
        'description': 'Big content',
        'milestone_id': 1,
        'weight': 4,
        'labels': ['Story']}, sudo='jdoe')
    gl_manager.project.labels.create.assert_called_once_with({
        'name': 'Story',
        'color': '#cccccc'})


def test_in_progress_issue_with_version(mocker):
    a2g.link_to_jira_source = False

    fakeJiraManager(mocker)

    jira_issue = fakeJiraIssue()
    jira_issue.fields.fixVersions.append('1.0')
    jira_issue.fields.status.name = 'In Progress'
    jira_issue.fields.status.raw.statusCategory.key = 'intermediate'
    jira_issue.fields.status.raw.statusCategory.color = 'yellow'

    gl_manager = fakeGitlabManager(mocker)
    gl_manager.project.labels.get.side_effect = GitlabGetError
    story_label = Label('Story')
    story_label.color = '#cccccc'
    wip_label = Label('In Progress')
    wip_label.color = None
    gl_manager.findLabel.side_effect = [story_label, wip_label]
    gl_milestone = mocker.MagicMock()
    gl_milestone.id = 1
    gl_manager.findMilestone.return_value = gl_milestone

    Issue().fillFromJira(jira_issue)

    gl_manager.project.issues.create.assert_called_once_with({
        'created_at': '2008-04-12T21:00:00',
        'title': 'Title',
        'assignee_ids': [1],
        'description': 'Big content',
        'milestone_id': 1,
        'weight': 4,
        'labels': ['Story', 'In Progress']
    }, sudo='jdoe')
    gl_manager.project.labels.create.assert_called_once_with({
        'name': 'In Progress',
        'color': '#0000ff'})


def test_resolved_issue_with_comments(mocker):
    a2g.link_to_jira_source = True

    fakeJiraManager(mocker)

    jira_issue = fakeJiraIssue()
    jira_issue.fields.comment = munchify({'comments': [{
        'body': 'Content',
        'created': '12/Apr/2008 9 PM',
        'author': {'key': 'jdoe'}}]})
    jira_issue.fields.resolution = True
    jira_issue.fields.resolutiondate = '2012-12-12 12:12'

    gl_manager = fakeGitlabManager(mocker)
    gl_milestone = mocker.MagicMock()
    gl_milestone.id = 1
    gl_manager.findMilestone.return_value = gl_milestone
    gl_issue = mocker.MagicMock()
    gl_issue.notes = mocker.MagicMock()
    gl_manager.project.issues.create.return_value = gl_issue

    Issue().fillFromJira(jira_issue)

    gl_manager.project.issues.create.assert_called_once_with({
        'created_at': '2008-04-12T21:00:00',
        'title': 'Title',
        'assignee_ids': [1],
        'description': 'Big content',
        'milestone_id': None,
        'weight': 4,
        'labels': ['Story']
    }, sudo='jdoe')
    gl_issue.notes.create.assert_has_calls([
        mocker.call(
            {'body': 'Content', 'created_at': '2008-04-12T21:00:00'},
            sudo='jdoe'),
        mocker.call({'body': 'Imported from [PRO-1](http://url/)'})])

    assert gl_issue.state_event == 'close'
    assert gl_issue.updated_at == '2012-12-12T12:12:00'
    assert gl_issue.save.call_count == 1

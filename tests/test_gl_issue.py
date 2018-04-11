import pytest
from munch import munchify
import atlassian2gitlab as a2g
from atlassian2gitlab.gl_resources import Issue


def fakeGitlabManager(mocker):
    mock = mocker.patch('atlassian2gitlab.managers.GitlabManager')
    mgr = mock.return_value
    mgr.project = mocker.MagicMock()
    mgr.project.issues = mocker.MagicMock()
    return mgr


def fakeJiraManager(mocker):
    mock = mocker.patch('atlassian2gitlab.managers.JiraManager')
    mgr = mock.return_value
    mgr.jira = mocker.MagicMock()
    mgr.getFieldId.return_value = 'customfield_10001'
    return mgr


class fakeMilestone(object):
    def __init__(self, id=1):
        self.id = id


class fakeUser(object):
    def __init__(self, id=1, name='jdoe'):
        self.id = id
        self.username = name


def test_get_issue_raise_exception():
    with pytest.raises(NotImplementedError):
        Issue().get()


def test_create(mocker):
    mgr = fakeGitlabManager(mocker)

    issue = Issue()
    issue.owner = mocker.MagicMock()
    issue.owner.username = 'jdoe'

    issue.setData('foo', 'bar')
    issue.save()

    mgr.project.issues.create.assert_called_once_with(
        {'foo': 'bar'},
        sudo='jdoe')
    assert issue._data == {}
    assert issue.toSave is False


def test_get_no_sprint(mocker):
    mgr = fakeJiraManager(mocker)

    jira_fields = munchify({})
    issue = Issue()

    assert issue.getSprint(jira_fields) is None


def test_get_sprint(mocker):
    mgr = fakeJiraManager(mocker)
    mgr.jira.sprint.return_value = 'Sprint 1'

    jira_fields = munchify({'customfield_10001': ['id=20,']})
    issue = Issue()

    assert issue.getSprint(jira_fields) == 'Sprint 1'
    mgr.jira.sprint.assert_called_once_with('20')


def test_set_milestone_from_sprint(mocker):
    mgr = fakeGitlabManager(mocker)
    issue = Issue()
    milestone = mocker.MagicMock()
    mgr.findMilestone.return_value = milestone

    issue.setMilestoneFromSprint('1.0')

    milestone.fillFromJiraSprint.assert_called_once_with('1.0')
    mgr.findMilestone.assert_called_once_with('1.0')


def test_set_milestone_from_version(mocker):
    mgr = fakeGitlabManager(mocker)
    issue = Issue()
    milestone = mocker.MagicMock()
    mgr.findMilestone.return_value = milestone

    issue.setMilestoneFromVersion('1.0')

    milestone.fillFromJiraVersion.assert_called_once_with('1.0')
    mgr.findMilestone.assert_called_once_with('1.0')


def test_set_weight(mocker):
    issue = Issue()

    mocker.patch.object(issue, 'getWeight')
    mocker.patch.object(issue, 'setData')

    issue.getWeight.return_value = 2

    issue.setWeight(2)

    issue.getWeight.assert_called_once_with(2)
    issue.setData.assert_called_once_with('weight', 2)


def test_set_owner(mocker):
    mgr = fakeGitlabManager(mocker)
    issue = Issue()
    mgr.findUser.return_value = 'John Doe'

    issue.setOwner('jdoe')

    mgr.findUser.assert_called_once_with('jdoe')
    assert issue.owner == 'John Doe'


class fakeJiraIssue(object):
    key = 'PRO-1'
    fields = munchify({
        'created': 'now',
        'summary': 'Title',
        'reporter': {'name': 'jdoe'},
        'assignee': {'name': 'jdoe'},
        'description': 'Big content',
        'fixVersions': [],
        'customfield_10001': 1,
        'issuetype': {'name': 'Story', 'iconUrl': 'http://url'}
    })

    def permalink(self):
        return 'http://url/'


def test_create_from_jira_issue_with_sprint(mocker):
    a2g.link_to_jira_source = False
    mgr = fakeJiraManager(mocker)
    user = fakeUser()
    issue = Issue()

    jira_issue = fakeJiraIssue()

    mocker.patch.object(issue, 'getSprint')
    mocker.patch.object(issue, 'setWeight')
    mocker.patch.object(issue, 'setMilestoneFromSprint')
    mocker.patch.object(issue, 'save')

    fakeGitlabManager(mocker).findUser.return_value = user
    issue.getSprint.return_value = 'Sprint 1'

    issue.fillFromJira(jira_issue)

    mgr.getFieldId.assert_called_once_with('Story Points')
    issue.setWeight.assert_called_once_with(1)
    issue.setMilestoneFromSprint.assert_called_once_with('Sprint 1')
    assert issue.save.call_count == 1


def test_create_from_jira_issue_with_version(mocker):
    a2g.link_to_jira_source = False
    mgr = fakeJiraManager(mocker)
    user = fakeUser()
    issue = Issue()

    jira_issue = fakeJiraIssue()
    jira_issue.fields.fixVersions.append('1.0')

    mocker.patch.object(issue, 'getSprint')
    mocker.patch.object(issue, 'setWeight')
    mocker.patch.object(issue, 'setMilestoneFromVersion')
    mocker.patch.object(issue, 'save')

    fakeGitlabManager(mocker).findUser.return_value = user
    issue.getSprint.return_value = None

    issue.fillFromJira(jira_issue)

    mgr.getFieldId.assert_called_once_with('Story Points')
    issue.setWeight.assert_called_once_with(1)
    issue.setMilestoneFromVersion.assert_called_once_with('1.0')
    assert issue.save.call_count == 1


def test_create_from_jira_issue_with_sprint(mocker):
    a2g.link_to_jira_source = True
    mgr = fakeJiraManager(mocker)
    user = fakeUser()

    issue = Issue()
    issue._item = mocker.MagicMock()
    issue._item.notes = mocker.MagicMock()

    jira_issue = fakeJiraIssue()
    jira_issue.fields.comment = munchify({'comments': [
        {'body': 'Content', 'created': 'now', 'author': {'key': 'jdoe'}}
    ]})

    mocker.patch.object(issue, 'getSprint')
    mocker.patch.object(issue, 'setWeight')
    mocker.patch.object(issue, 'setMilestoneFromSprint')
    mocker.patch.object(issue, 'save')

    fakeGitlabManager(mocker).findUser.return_value = user
    issue.getSprint.return_value = 'Sprint 1'

    issue.fillFromJira(jira_issue)

    mgr.getFieldId.assert_called_once_with('Story Points')
    issue.setWeight.assert_called_once_with(1)
    issue.setMilestoneFromSprint.assert_called_once_with('Sprint 1')
    assert issue.save.call_count == 1
    assert issue._item.notes.create.call_count == 2

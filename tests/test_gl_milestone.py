import logging
from munch import munchify
from atlassian2gitlab.gl_resources import ProjectMilestone


class fakeGlMilestone(object):
    id = 1
    title = '1.0'
    due_date = None
    state = 'active'
    state_event = None

    def save(self):
        pass


def fakeManager(mocker):
    mock = mocker.patch('atlassian2gitlab.managers.GitlabManager')
    mgr = mock.return_value
    mgr.project = mocker.MagicMock()
    mgr.project.milestones = mocker.MagicMock()
    return mgr


def test_milestone(mocker):
    mgr = fakeManager(mocker)
    mgr.project.milestones.list.return_value = [fakeGlMilestone()]

    mi = ProjectMilestone('1.0')

    assert mi.id == 1


def test_create_milestone(mocker):
    mgr = fakeManager(mocker)
    mgr.project.milestones.list.return_value = []
    mgr.project.milestones.create.return_value = fakeGlMilestone()

    mi = ProjectMilestone('1.0')

    assert mi.id == 1
    assert mgr.project.milestones.create.call_count == 1


def test_fill_milestone_from_jira_sprint(mocker):
    mgr = fakeManager(mocker)
    mi = ProjectMilestone('1.0')
    mi._item = fakeGlMilestone()

    sprint = munchify({'endDate': '2008-04-12', 'state': 'CLOSED'})

    mi.fillFromJiraSprint(sprint)

    assert mi.due_date == '2008-04-12'
    assert mi.state_event == 'close'


def test_fill_milestone_from_jira_version(mocker):
    mgr = fakeManager(mocker)
    mi = ProjectMilestone('1.0')
    mi._item = fakeGlMilestone()

    version = munchify({'releaseDate': '12/Apr/08 09:00 PM', 'released': True})

    mi.fillFromJiraVersion(version)

    assert mi.due_date == '2008-04-12'
    assert mi.state_event == 'close'

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
    mgr = mocker.MagicMock()
    mgr.project = mocker.MagicMock()
    mgr.project.milestones = mocker.MagicMock()
    return mgr


def test_get_milestone(mocker):
    mgr = fakeManager(mocker)
    mgr.project.milestones.list.return_value = [fakeGlMilestone()]

    mi = ProjectMilestone('1.0', manager=mgr)
    mocker.spy(mi, 'create')

    assert mi.get().id == 1
    assert mi.create.call_count == 0


def test_create_on_get_missing_milestone(mocker):
    mgr = fakeManager(mocker)
    mgr.project.milestones.list.return_value = []
    mgr.project.milestones.create.return_value = fakeGlMilestone()

    mi = ProjectMilestone('1.0', manager=mgr)
    mocker.spy(mi, 'create')

    assert mi.get().id == 1
    assert mi.create.call_count == 1


def test_fill_milestone_from_jira_sprint(mocker):
    mgr = fakeManager(mocker)
    mi = ProjectMilestone('1.0', manager=mgr)
    mi._item = fakeGlMilestone()

    sprint = munchify({'endDate': 'now', 'state': 'CLOSED'})

    mocker.spy(mi, 'save')
    mi.fillFromJiraSprint(sprint)

    assert mi.save.call_count == 1
    assert mi.toSave is False
    assert mi.get().due_date == 'now'
    assert mi.get().state_event == 'close'


def test_fill_milestone_from_jira_version(mocker):
    mgr = fakeManager(mocker)
    mi = ProjectMilestone('1.0', manager=mgr)
    mi._item = fakeGlMilestone()

    version = munchify({'releaseDate': 'now', 'released': True})

    mocker.spy(mi, 'save')
    mi.fillFromJiraVersion(version)

    assert mi.save.call_count == 1
    assert mi.toSave is False
    assert mi.get().due_date == 'now'
    assert mi.get().state_event == 'close'

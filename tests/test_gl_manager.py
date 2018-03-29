import atlassian2gitlab as a2g
from atlassian2gitlab.managers import GitlabManager
from munch import munchify


def fakeProject(mocker):
    p = mocker.MagicMock()
    p.milestones = mocker.MagicMock()
    return p


def test_gitlab_manager(mocker):
    a2g.gitlab_repo = 'fake/project'

    manager = GitlabManager()
    manager._gitlab = None
    manager._project = None
    mock = mocker.patch('atlassian2gitlab.clients.Gitlab')

    manager.gitlab

    assert manager.project._repo == 'fake/project'
    assert mock.call_count == 1


def test_use_current_user_if_user_not_found(mocker):
    manager = GitlabManager()
    gl = mocker.MagicMock()
    manager._gitlab = gl

    gl.users = mocker.MagicMock()
    gl.users.list.return_value = ['not', 'found']
    gl.user = mocker.MagicMock()
    gl.user.username = 'current'

    user = manager.findUser('user')
    assert user._username == 'current'
    assert gl.auth.call_count == 1


def test_find_user(mocker):
    manager = GitlabManager()
    gl = mocker.MagicMock()
    manager._gitlab = gl

    gl.users = mocker.MagicMock()
    gl.users.list.return_value = ['me']

    user = manager.findUser('me')
    assert user._username == 'me'


def test_find_existing_milestone(mocker):
    project = fakeProject(mocker)
    project.milestones.list.return_value = [munchify({'title': '1.0'})]
    manager = GitlabManager()
    manager._project = project

    assert manager.findMilestone('1.0')._title == '1.0'


def test_find_milestone():
    manager = GitlabManager()
    assert manager.findMilestone('2.0')._title == '2.0'


def test_gitlab_upload(mocker):
    project = munchify({
        'upload': lambda filename, filedata: 'Gitlab attachment'
    })
    manager = GitlabManager()
    manager._project = project
    attachment = mocker.MagicMock()
    attachment.id = '1'
    attachment.filename = 'blah.jpg'
    attachment.get.return_value = 'Data'

    assert manager.attachFile(attachment) == 'Gitlab attachment'
    assert attachment.get.call_count == 1
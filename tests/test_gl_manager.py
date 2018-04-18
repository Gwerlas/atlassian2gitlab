import atlassian2gitlab as a2g
from atlassian2gitlab.managers import GitlabManager
from munch import munchify


def fakeProject(mocker):
    p = mocker.MagicMock()
    p.milestones = mocker.MagicMock()
    return p


def test_use_current_user_if_user_not_found(mocker):
    manager = GitlabManager()
    gl = mocker.MagicMock()
    manager._client = gl

    gl.users = mocker.MagicMock()
    gl.users.list.return_value = ['not', 'found']
    gl.user = mocker.MagicMock()
    gl.user.username = 'current'

    user = manager.findUser('user')
    assert user.username == 'current'
    assert gl.auth.call_count == 1


def test_find_user(mocker):
    manager = GitlabManager()
    gl = mocker.MagicMock()
    manager._client = gl

    gl.users = mocker.MagicMock()
    gl.users.list.return_value = ['me']

    user = manager.findUser('me')
    assert user.username == 'me'


def test_find_existing_milestone(mocker):
    project = fakeProject(mocker)
    project.milestones.list.return_value = [munchify({'title': '1.0'})]
    manager = GitlabManager()
    manager._project = project

    assert manager.findMilestone('1.0').title == '1.0'


def test_find_milestone():
    manager = GitlabManager()
    assert manager.findMilestone('2.0').title == '2.0'


def test_client_upload(mocker):
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

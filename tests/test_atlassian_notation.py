from atlassian2gitlab.at_objects import JiraNotation
from munch import munchify


def test_text_breaks():
    notation = JiraNotation('Blah\r\nBlah', None)
    assert notation.toMarkdown() == 'Blah  \nBlah'


def test_jira_notation_to_markdown(mocker, datadir):
    user = munchify({'username': 'gwerlas'})
    manager = mocker.patch('atlassian2gitlab.JiraManager')
    given = datadir['given.txt'].read_text('utf-8')
    expected = datadir['expected.txt'].read_text('utf-8')
    notation = JiraNotation(given, manager)

    manager.findUser.return_value = user

    assert notation.toMarkdown() == expected

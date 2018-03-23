from atlassian2gitlab.at_resources import JiraNotationConverter
from munch import munchify
import re


def test_jira_notation_to_markdown(mocker, datadir):
    user = munchify({'username': 'gwerlas'})
    mock = mocker.patch('atlassian2gitlab.managers.GitlabManager')
    given = datadir['given.txt'].read_text('utf-8')
    expected = datadir['expected.txt'].read_text('utf-8')
    converter = JiraNotationConverter(munchify({'fields': {'attachment': []}}))

    manager = mock.return_value
    manager.findUser.return_value = user

    assert converter.toMarkdown(given) == expected


def test_attachments_to_markdown(mocker):
    mock = mocker.patch('atlassian2gitlab.managers.GitlabManager')
    converter = JiraNotationConverter(
        munchify({'fields': {'attachment': [
            {'filename': 'blah.jpg'}
        ]}}))

    given = converter.toMarkdown('!blah.jpe!')

    assert given == ''

    expected = '[alt](blah.jpg)'
    manager = mock.return_value
    manager.attachFile.return_value = {'markdown': expected}

    assert converter.toMarkdown('!blah.jpg!') == expected
    assert converter.toMarkdown('!blah.jpg|thumbnail!') == expected

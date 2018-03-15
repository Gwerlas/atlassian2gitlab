from atlassian2gitlab.at_resources import JiraNotationConverter
from munch import munchify
import re


def test_text_breaks():
    converter = JiraNotationConverter(
        None,
        munchify({'fields': {'attachment': []}}))
    assert converter.toMarkdown('Blah\r\nBlah') == 'Blah  \nBlah'


def test_jira_notation_to_markdown(mocker, datadir):
    user = munchify({'username': 'gwerlas'})
    manager = mocker.patch('atlassian2gitlab.JiraManager')
    given = datadir['given.txt'].read_text('utf-8')
    expected = datadir['expected.txt'].read_text('utf-8')
    converter = JiraNotationConverter(
        manager,
        munchify({'fields': {'attachment': []}}))

    manager.findUser.return_value = user

    assert converter.toMarkdown(given) == expected


def test_attachments_to_markdown(mocker):
    manager = mocker.patch('atlassian2gitlab.Manager')
    converter = JiraNotationConverter(
        manager,
        munchify({'fields': {'attachment': [
            {'filename': 'blah.jpg'}
        ]}}))

    given = converter.toMarkdown('!blah.jpe!')

    assert given == ''

    expected = '[alt](blah.jpg)'
    manager.attachFile.return_value = {'markdown': expected}

    assert converter.toMarkdown('!blah.jpg!') == expected
    assert converter.toMarkdown('!blah.jpg|thumbnail!') == expected

from atlassian2gitlab.jira import Jira


def test_active_issues(mocker):
    jira = mocker.patch('atlassian2gitlab.jira.Jira')

    Jira.active_issues(jira, 'KEY')
    s = 'project=KEY AND (resolution=Unresolved OR Sprint in openSprints())'
    jira.search_issues.assert_called_once_with(s)

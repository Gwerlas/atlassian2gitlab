import sys
from atlassian2gitlab.options import Options

EXPECTED_ARGS = ['atlassian2gitlab',
                 '--gitlab-token', 'foo',
                 '--gitlab-repo', 'bar',
                 '--atlassian-username', 'john@doe.tld',
                 '--atlassian-password', 'secret',
                 '--jira-project-key', 'KEY']


def test_gl_url_default():
    sys.argv = EXPECTED_ARGS
    assert Options().values.GL_URL == 'https://gitlab.com/'


def test_gl_url():
    sys.argv = EXPECTED_ARGS
    sys.argv.extend(['--gitlab-url', 'https://test.tld'])
    assert Options().values.GL_URL == 'https://test.tld'


def test_gl_token():
    sys.argv = EXPECTED_ARGS
    assert Options().values.GL_TOKEN == 'foo'


def test_gl_repo():
    sys.argv = EXPECTED_ARGS
    assert Options().values.GL_REPO == 'bar'


def test_at_user():
    sys.argv = EXPECTED_ARGS
    assert Options().values.AT_USER == 'john@doe.tld'


def test_at_pass():
    sys.argv = EXPECTED_ARGS
    assert Options().values.AT_PASS == 'secret'


def test_jira_url_default():
    sys.argv = EXPECTED_ARGS
    assert Options().values.JIRA_URL == 'https://jira.atlassian.com'


def test_jira_url():
    sys.argv = EXPECTED_ARGS
    sys.argv.extend(['--jira-url', 'https://test.tld'])
    assert Options().values.JIRA_URL == 'https://test.tld'


def test_jira_project_key():
    sys.argv = EXPECTED_ARGS
    assert Options().values.JIRA_PROJECT_KEY == 'KEY'

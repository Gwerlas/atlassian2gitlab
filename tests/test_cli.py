import sys
from atlassian2gitlab.cli import CLI

EXPECTED_ARGS = ['atlassian2gitlab',
                 '--gitlab-token', 'foo',
                 '--gitlab-repo', 'bar',
                 '--atlassian-username', 'john@doe.tld',
                 '--atlassian-password', 'secret',
                 '--jira-project-key', 'KEY']


def test_gl_url_default():
    sys.argv = EXPECTED_ARGS
    assert CLI().config.GL_URL == 'https://gitlab.com/'


def test_gl_url():
    sys.argv = EXPECTED_ARGS
    sys.argv.extend(['--gitlab-url', 'https://test.tld'])
    assert CLI().config.GL_URL == 'https://test.tld'


def test_gl_token():
    sys.argv = EXPECTED_ARGS
    assert CLI().config.GL_TOKEN == 'foo'


def test_gl_repo():
    sys.argv = EXPECTED_ARGS
    assert CLI().config.GL_REPO == 'bar'


def test_at_user():
    sys.argv = EXPECTED_ARGS
    assert CLI().config.AT_USER == 'john@doe.tld'


def test_at_pass():
    sys.argv = EXPECTED_ARGS
    assert CLI().config.AT_PASS == 'secret'


def test_jira_url_default():
    sys.argv = EXPECTED_ARGS
    assert CLI().config.JIRA_URL == 'https://jira.atlassian.com'


def test_jira_url():
    sys.argv = EXPECTED_ARGS
    sys.argv.extend(['--jira-url', 'https://test.tld'])
    assert CLI().config.JIRA_URL == 'https://test.tld'


def test_jira_project_key():
    sys.argv = EXPECTED_ARGS
    assert CLI().config.JIRA_PROJECT_KEY == 'KEY'


def test_warn_is_yellow(capsys):
    import logging
    CLI()
    logging.warn('message')
    out, err = capsys.readouterr()
    assert err == '\x1b[33mWARNING message\x1b[0m\n'

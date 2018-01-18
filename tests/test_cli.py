import sys
from atlassian2gitlab.cli import CLI

FLUSH_ARGS = ['flush-gitlab',
              '--gitlab-token', 'foo',
              '--gitlab-repo', 'bar']

MIGRATION_ARGS = ['atlassian2gitlab',
                  '--gitlab-token', 'foo',
                  '--gitlab-repo', 'bar',
                  '--atlassian-username', 'john@doe.tld',
                  '--atlassian-password', 'secret',
                  '--jira-project-key', 'KEY']


def test_gl_url_default():
    sys.argv = FLUSH_ARGS
    assert CLI().flushConfig.GL_URL == 'https://gitlab.com/'


def test_gl_url():
    sys.argv = FLUSH_ARGS
    sys.argv.extend(['--gitlab-url', 'https://test.tld'])
    assert CLI().flushConfig.GL_URL == 'https://test.tld'


def test_gl_token():
    sys.argv = FLUSH_ARGS
    assert CLI().flushConfig.GL_TOKEN == 'foo'


def test_gl_repo():
    sys.argv = FLUSH_ARGS
    assert CLI().flushConfig.GL_REPO == 'bar'


def test_at_user():
    sys.argv = MIGRATION_ARGS
    assert CLI().migrationConfig.AT_USER == 'john@doe.tld'


def test_at_pass():
    sys.argv = MIGRATION_ARGS
    assert CLI().migrationConfig.AT_PASS == 'secret'


def test_jira_url_default():
    sys.argv = MIGRATION_ARGS
    assert CLI().migrationConfig.JIRA_URL == 'https://jira.atlassian.com'


def test_jira_url():
    sys.argv = MIGRATION_ARGS
    sys.argv.extend(['--jira-url', 'https://test.tld'])
    assert CLI().migrationConfig.JIRA_URL == 'https://test.tld'


def test_jira_project_key():
    sys.argv = MIGRATION_ARGS
    assert CLI().migrationConfig.JIRA_PROJECT_KEY == 'KEY'


def test_warn_is_yellow(capsys):
    import logging
    CLI()
    logging.warn('message')
    out, err = capsys.readouterr()
    assert err == '\x1b[33mWARNING  root           message\x1b[0m\n'

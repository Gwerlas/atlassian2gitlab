import sys
import pytest
from atlassian2gitlab.cli import CLI, GitlabConfig, JiraConfig


def test_gitlabconfig(mocker):
    config = mocker.MagicMock()
    config.getboolean.return_value = True
    config.get.return_value = 'the url'

    gl_config = GitlabConfig(config)

    assert gl_config.ssl_verify is True
    assert gl_config.url is 'the url'


def test_jiraconfig(mocker):
    config = mocker.MagicMock()
    config.getboolean.return_value = True
    config.get.return_value = 'the url'

    jira_config = JiraConfig(config)

    assert jira_config.ssl_verify is True
    assert jira_config.url is 'the url'


def test_exit_if_config_arg_missing(capsys):
    with pytest.raises(SystemExit):
        CLI().flushConfig
    err = capsys.readouterr()[1]
    assert "error" in err


def test_configparse(mocker):
    config = mocker.MagicMock()
    mocker.patch('configparser.ConfigParser', return_value=config)

    CLI()._configparse('path/to/file')
    config.read.assert_called_once_with('path/to/file')


def test_flush_config(mocker):
    cli = CLI()
    arg_parser = mocker.MagicMock()
    mocker.patch.object(cli, '_argparse', return_value=arg_parser)

    gl_config = mocker.MagicMock()
    mocker.patch.object(cli, '_configparse', return_value={'gitlab': gl_config})

    cli.flushConfig

    assert arg_parser.parse_args.call_count == 1


def test_migration_config(mocker):
    cli = CLI()
    arg_parser = mocker.MagicMock()
    mocker.patch.object(cli, '_argparse', return_value=arg_parser)

    returns = {'gitlab': mocker.MagicMock(), 'jira': mocker.MagicMock()}
    mocker.patch.object(cli, '_configparse', return_value=returns)

    cli.migrationConfig

    assert arg_parser.parse_args.call_count == 1

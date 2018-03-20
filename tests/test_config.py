import pytest
import argparse
import configparser
from munch import munchify
from atlassian2gitlab.cli import CLI, Config


def test_exit_if_config_arg_missing(capsys):
    with pytest.raises(SystemExit):
        CLI().initConfig('This is my test !')
    err = capsys.readouterr()[1]
    assert "error" in err


def test_init_config(mocker):
    cli = CLI()
    mocker.patch('argparse.ArgumentParser')
    mocker.patch('configparser.ConfigParser')
    mocker.patch('atlassian2gitlab.cli.Config')

    parser = mocker.MagicMock()
    parser.parse_args.return_value = munchify({'config': 'my-config.ini'})
    argparse.ArgumentParser.return_value = parser
    config = mocker.MagicMock()
    configparser.ConfigParser.return_value = config

    cli.initConfig('This is my test !')

    assert parser.add_argument.call_count == 3
    assert parser.parse_args.call_count == 1
    config.read.assert_called_once_with('my-config.ini')

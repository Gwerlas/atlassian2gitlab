import pytest
import argparse
import configparser
from munch import munchify
from atlassian2gitlab import cli
import logging


def test_logging(capsys):
    with pytest.raises(SystemExit):
        cli.configure('This is my test !')
    err = capsys.readouterr()[1]
    assert "error" in err

    logging.warn('message')
    err = capsys.readouterr()[1]
    assert err == '\x1b[33mWARNING  root           message\x1b[0m\n'


def test_config(mocker):
    mocker.patch('argparse.ArgumentParser')
    mocker.patch('configparser.ConfigParser')
    mocker.patch('atlassian2gitlab.cli.Config')

    parser = mocker.MagicMock()
    parser.parse_args.return_value = munchify({
        'config': 'my-config.ini',
        'debug': False})
    argparse.ArgumentParser.return_value = parser
    config = mocker.MagicMock()
    configparser.ConfigParser.return_value = config

    cli.configure('This is my test !')

    assert parser.add_argument.call_count == 3
    assert parser.parse_args.call_count == 1
    config.read.assert_called_once_with('my-config.ini')

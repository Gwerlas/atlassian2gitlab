import configparser
import pytest
from munch import munchify
from atlassian2gitlab import cli


def test_logging(capsys):
    with pytest.raises(SystemExit):
        cli.configure('This is my test !')
    err = capsys.readouterr()[1]
    assert "error" in err


def test_config(mocker):
    ap = mocker.patch('argparse.ArgumentParser').return_value
    cp = mocker.patch('configparser.ConfigParser').return_value
    mocker.patch('atlassian2gitlab.cli.Config')

    ap.parse_args.return_value = munchify({
        'config': 'my-config.ini',
        'flush': False})

    cli.configure('This is my test !')

    assert ap.add_argument.call_count == 3
    assert ap.parse_args.call_count == 1
    cp.read.assert_called_once_with('my-config.ini')

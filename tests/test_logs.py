import configparser
import logging
from atlassian2gitlab import cli


def test_loggers_config(mocker):
    config = configparser.ConfigParser()
    config.read_dict({
        'gitlab': {'token': '', 'repo': ''},
        'jira': {'url': '', 'key': '', 'username': '', 'password': ''},
        'loggers': {'keys': 'root'},
        'logger_root': {'handlers': 'stream', 'level': 'DEBUG'},
        'handlers': {'keys': 'stream'},
        'handler_stream': {
            'class': 'StreamHandler', 'args': '()', 'formatter': 'stream'},
        'formatters': {'keys': 'stream'},
        'formatter_stream': {'format': '%(message)s'},
    })

    cli.Config(config)

    assert logging.getLogger().getEffectiveLevel() == logging.DEBUG

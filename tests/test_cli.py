from atlassian2gitlab.cli import CLI


def test_warn_is_yellow(capsys):
    import logging
    CLI()
    logging.warn('message')
    err = capsys.readouterr()[1]
    assert err == '\x1b[33mWARNING  root           message\x1b[0m\n'

import atlassian2gitlab as a2g


class Config(object):
    """
    Wrap the config parser to set up the module

    >>> import atlassian2gitlab as a2g
    >>> import configparser
    >>> config = configparser.ConfigParser()
    >>> config['DEFAULT'] = {'debug': 'on'}
    >>> config['gitlab'] = {
    ...     'url': 'http://my-gitlab.local',
    ...     'token': 'get-it-from-your-profile',
    ...     'repo': 'fake/project'}
    >>> config['jira'] = {
    ...     'key': 'PRO',
    ...     'url': 'http://my-jira.local',
    ...     'username': 'jdoe',
    ...     'password': 'secret'}
    >>> config['story_points'] = {'5': '4'}
    >>> config['user_map'] = {'jira': 'gitlab'}
    >>> c = Config(config)
    >>> a2g.debug
    True
    >>> a2g.ssl_verify
    True
    >>> a2g.gitlab_url
    'http://my-gitlab.local'
    >>> a2g.gitlab_token
    'get-it-from-your-profile'
    >>> a2g.gitlab_repo
    'fake/project'
    >>> a2g.jira_key
    'PRO'
    >>> a2g.jira_url
    'http://my-jira.local'
    >>> a2g.jira_username
    'jdoe'
    >>> a2g.jira_password
    'secret'

    If a section named `user_map` is present, we use it as a map for
    user conversion between the Atlassian suite and Gitlab.

    >>> a2g.user_map['jira']
    'gitlab'

    If a section named `story_points` is present, we use it as a map for
    conversions in Gitlab issue weight.
    Configparser send DEFAULTSECT, so we have to ignore no numerical keys.

    >>> 'debug' in a2g.storyPoint_map
    False
    >>> 'key' in a2g.storyPoint_map
    False
    >>> a2g.storyPoint_map[5]
    4
    """
    def __init__(self, config):
        defaults = config['DEFAULT']
        debug = defaults.getboolean('debug', fallback=False)
        if debug:
            a2g.debug = True
        a2g.ssl_verify = defaults.getboolean('ssl_verify', fallback=True)
        if 'story_points' in config:
            self.mapStoryPoints(config['story_points'])
        if 'user_map' in config:
            a2g.user_map = config['user_map']

        gl_config = config['gitlab']
        a2g.gitlab_token = gl_config.get('token')
        a2g.gitlab_url = gl_config.get('url', fallback='https://gitlab.com/')
        a2g.gitlab_repo = gl_config.get('repo')

        ji_config = config['jira']
        a2g.jira_url = ji_config.get('url')
        a2g.jira_key = ji_config.get('key')
        a2g.jira_username = ji_config.get('username')
        a2g.jira_password = ji_config.get('password')

    def mapStoryPoints(self, dict):
        """
        Add/replace values in a2g.storyPoint_map dict

        >>> import atlassian2gitlab as a2g
        >>> import configparser
        >>> config = configparser.ConfigParser()
        >>> config['DEFAULT'] = {}
        >>> config['gitlab'] = {}
        >>> config['jira'] = {}
        >>> config['story_points'] = {'5': '4'}
        >>> c = Config(config)
        >>> c.mapStoryPoints({'7': '4', 'blah': 'blah'})
        >>> a2g.storyPoint_map[7]
        4
        >>> 'blah' in a2g.storyPoint_map
        False
        """
        for k, v in dict.items():
            if not k.isdigit():
                continue
            key = int(k)
            value = int(v)
            a2g.storyPoint_map[key] = value


def configure(description):
    from colorlog import ColoredFormatter
    import logging

    formatter = ColoredFormatter(
        "%(log_color)s%(levelname)-8s %(name)-14s %(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    import argparse
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '-c', '--config',
        help='Config file path',
        required=True)
    parser.add_argument(
        '-d', '--debug',
        help='Display debug messages',
        action='store_true',
        default=False)
    parser.add_argument(
        '-V', '--version',
        help='Show version and exit',
        action='version',
        version='Atlassian2Gitlab {}'.format(a2g.__version__))
    args = parser.parse_args()
    a2g.debug = args.debug

    import configparser
    config = configparser.ConfigParser()
    config.read(args.config)
    Config(config)

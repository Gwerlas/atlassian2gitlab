class Config(object):
    def __init__(self, config):
        self.ssl_verify = config.getboolean('ssl_verify', fallback=True)


class AtlassianConfig(Config):
    def __init__(self, config):
        Config.__init__(self, config)
        self.username = config['username']
        self.password = config['password']


class JiraConfig(AtlassianConfig):
    def __init__(self, config):
        AtlassianConfig.__init__(self, config)
        self.url = config.get('url', fallback='https://jira.atlassian.com')
        self.key = config['key']


class GitlabConfig(Config):
    def __init__(self, config):
        Config.__init__(self, config)
        self.token = config['token']
        self.url = config.get('url', fallback='https://gitlab.com/')
        self.repo = config['repo']


class CLI(object):
    """Read and parse commandline arguments"""
    def __init__(self):
        self._configure_logger()

    def _configure_logger(self):
        import logging
        from colorlog import ColoredFormatter

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

    def _argparse(self, description):
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
            version=self.version)
        return parser

    def _configparse(self, file):
        import configparser
        config = configparser.ConfigParser()
        config.read(file)
        return config

    @property
    def flushConfig(self):
        args = self._argparse('Flush your Gitlab').parse_args()
        config = self._configparse(args.config)
        args.gitlab = GitlabConfig(config['gitlab'])
        return args

    @property
    def migrationConfig(self):
        description = 'Migrate from the Atlassian suite to Gitlab'
        args = self._argparse(description).parse_args()
        config = self._configparse(args.config)
        args.gitlab = GitlabConfig(config['gitlab'])
        args.jira = JiraConfig(config['jira'])
        if 'user_map' in config:
            args.user_map = config['user_map']
        return args

    @property
    def version(self):
        import atlassian2gitlab
        return 'Atlassian2Gitlab {}'.format(atlassian2gitlab.__version__)

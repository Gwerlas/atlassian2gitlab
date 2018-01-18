import argparse


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

    def _baseConfig(self, description):
        parser = argparse.ArgumentParser(
            description=description,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        parser.add_argument(
            '--gitlab-url',
            dest='GL_URL',
            help='Gitlab URL',
            default='https://gitlab.com/')
        parser.add_argument(
            '--gitlab-token',
            dest='GL_TOKEN',
            help='Access Token for Gitlab',
            required=True)
        parser.add_argument(
            '--gitlab-repo',
            dest='GL_REPO',
            help='Gitlab project name',
            required=True)

        parser.add_argument(
            '--ssl-no-verify',
            dest='SSL_NO_VERIFY',
            help='Do not verify SSL certificate (not recommanded)',
            action='store_true',
            default=False)
        parser.add_argument(
            '--debug',
            dest='DEBUG',
            help='Display debug messages',
            action='store_true',
            default=False)

        return parser

    @property
    def flushConfig(self):
        return self._baseConfig('Flush your Gitlab').parse_args()

    @property
    def migrationConfig(self):
        parser = self._baseConfig('Migrate from the Atlassian suite to Gitlab')

        parser.add_argument(
            '--atlassian-username',
            dest='AT_USER',
            help='Atlassian user name',
            required=True)
        parser.add_argument(
            '--atlassian-password',
            dest='AT_PASS',
            help='Atlassian password',
            required=True)

        parser.add_argument(
            '--jira-url',
            dest='JIRA_URL',
            help='Jira URL',
            default='https://jira.atlassian.com')
        parser.add_argument(
            '--jira-project-key',
            dest='JIRA_PROJECT_KEY',
            help='Jira Project Key',
            required=True)

        return parser.parse_args()

import argparse


class Options(object):
    """Read and parse commandline arguments"""
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description='Migrate from the Atlassian suite to Gitlab.',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        self.parser.add_argument(
            '--gitlab-url',
            dest='GL_URL',
            help='Gitlab URL',
            nargs='?',
            default='https://gitlab.com/')
        self.parser.add_argument(
            '--gitlab-token',
            dest='GL_TOKEN',
            help='Access Token for Gitlab',
            required=True)
        self.parser.add_argument(
            '--gitlab-repo',
            dest='GL_REPO',
            help='Gitlab project name',
            required=True)

        self.parser.add_argument(
            '--atlassian-username',
            dest='AT_USER',
            help='Atlassian user name',
            required=True)
        self.parser.add_argument(
            '--atlassian-password',
            dest='AT_PASS',
            help='Atlassian password',
            required=True)

        self.parser.add_argument(
            '--jira-url',
            dest='JIRA_URL',
            help='Jira URL',
            nargs='?',
            default='https://jira.atlassian.com')
        self.parser.add_argument(
            '--jira-project-key',
            dest='JIRA_PROJECT_KEY',
            help='Jira Project Key',
            required=True)

        self.parser.add_argument(
            '--ssl-no-verify',
            dest='SSL_NO_VERIFY',
            help='Do not verify SSL certificate (not recommanded)')

    @property
    def values(self):
        return self.parser.parse_args()

from atlassian2gitlab.gl_objects import Project
from atlassian2gitlab.exceptions import A2GException
import jira
from gitlab import Gitlab
import logging
import requests


__version__ = 0.1


logger = logging.getLogger(__name__)
session = requests.Session()


class Manager(object):
    _gitlab = None
    _project = None

    def __init__(self, gitlab_url, gitlab_token, gitlab_repo,
                 debug=False, ssl_verify=True):
        self.debug = debug
        self.ssl_verify = ssl_verify
        self.gitlab_repo = gitlab_repo
        self.gitlab_token = gitlab_token
        self.gitlab_url = gitlab_url

    @property
    def gitlab(self):
        if not self._gitlab:
            self._gitlab = Gitlab(self.gitlab_url,
                                  private_token=self.gitlab_token,
                                  ssl_verify=self.ssl_verify,
                                  api_version=4,
                                  session=session)
            if self.debug:
                self._gitlab.enable_debug()
        return self._gitlab

    @property
    def project(self):
        if not self._project:
            self._project = Project(self.gitlab_repo, self.gitlab)
        return self._project


class AtlassianManager(Manager):
    def __init__(self, url, key, username, password, *args, **kwargs):
        self.url = url
        self.key = key
        self.username = username
        self.password = password
        Manager.__init__(self, *args, **kwargs)


class JiraManager(AtlassianManager):
    """
    Manage issues
    """
    _jira = None

    @property
    def jira(self):
        if not self._jira:
            self._jira = jira.JIRA(self.url,
                                   options={'verify': self.ssl_verify},
                                   basic_auth=(self.username, self.password))
        return self._jira

    def activeIssues(self):
        jql = 'project={}'.format(self.key)
        jql += ' AND (resolution=Unresolved OR Sprint in openSprints())'
        return self.jira.search_issues(jql)

    def cp(self):
        issues = self.activeIssues()
        total = len(issues)
        if total == 0:
            logger.info('Nothing to do')
            return self

        i = 0
        for issue in issues:
            try:
                self.project.addIssue(issue.fields)
                i += 1
            except A2GException as e:
                logger.warning('Skip issue %s: %s', issue.key, e)

        if i == total:
            logger.info('All %d issues migrated', total)
        elif i == 0:
            logger.error('Any issues migrated')
        else:
            logger.warn('%d/%d issues migrated', i, len(issues))

        return self

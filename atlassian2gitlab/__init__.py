from atlassian2gitlab.gl_objects import Project
from atlassian2gitlab.exceptions import A2GException
import jira
from gitlab import Gitlab
import logging
import requests


debug = False
gitlab_repo = None
gitlab_token = None
gitlab_url = None
jira_project_key = None
jira_url = None
atlassian_user = None
atlassian_pass = None
ssl_verify = True


logger = logging.getLogger(__name__)
session = requests.Session()


class Manager(object):
    _gitlab = None
    _project = None

    @property
    def gitlab(self):
        if not self._gitlab:
            self._gitlab = Gitlab(gitlab_url,
                                  private_token=gitlab_token,
                                  ssl_verify=ssl_verify,
                                  api_version=4,
                                  session=session)
            if debug:
                self._gitlab.enable_debug()
        return self._gitlab

    @property
    def project(self):
        if not self._project:
            self._project = Project(gitlab_repo, self.gitlab)
        return self._project


class JiraManager(Manager):
    """
    Manage issues
    """
    _jira = None

    @property
    def jira(self):
        if not self._jira:
            self._jira = jira.JIRA(jira_url,
                                   options={'verify': ssl_verify},
                                   basic_auth=(atlassian_user, atlassian_pass))
        return self._jira

    def activeIssues(self):
        jql = 'project={}'.format(jira_project_key)
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

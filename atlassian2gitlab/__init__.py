from atlassian2gitlab.gl_objects import Project, User
from atlassian2gitlab.exceptions import A2GException
import jira
from gitlab import Gitlab
import logging
import requests


__version__ = 0.2


logger = logging.getLogger(__name__)
session = requests.Session()
user_map = {}
storyPoint_map = {
    1.0: 1,
    2.0: 2,
    3.0: 3,
    5.0: 4,
    8.0: 5,
    13.0: 6,
    20.0: 7,
    40.0: 8,
    100.0: 9
}


class Manager(object):
    _gitlab = None
    _project = None
    _attachments = {}
    _milestones = {}
    _users = {}

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
            self._project = Project(self.gitlab_repo, self)
        return self._project

    def findUser(self, name):
        username = user_map.get(name, name)
        if username not in self._users:
            self._users[username] = User(username, self)
        return self._users[username]

    def findMilestone(self, obj):
        """
        Find Gitlab Milestone corresponding to the given object

        Returns:
            gitlab.v4.objects.Milestone
        """
        title = str(obj)
        if title not in self._milestones:
            for m in self.project.milestones.list(search=title):
                self._milestones[m.title] = m
        if title not in self._milestones:
            m = self.project.addMilestone(obj)
            self._milestones[m.title] = m
        return self._milestones[title]

    def attachFile(self, attachment):
        """
        Upload Jira attachment to the Gitlab project

        The filename is prepended by the Jira attachment ID because the same
        name can be used in different Jira issues.

        Returns:
            dict: A ``dict`` with the keys:
                * ``alt`` - The alternate text for the upload
                * ``url`` - The direct url to the uploaded file
                * ``markdown`` - Markdown for the uploaded file
        """
        id = str(attachment.id)
        if id not in self._attachments:
            a = self.project.upload(
                filename='_'.join([attachment.id, attachment.filename]),
                filedata=attachment.get())
            self._attachments[id] = a
        return self._attachments[id]


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
    _sprintCustomField = None

    @property
    def jira(self):
        if not self._jira:
            self._jira = jira.JIRA(
                self.url,
                options={'verify': self.ssl_verify},
                basic_auth=(self.username, self.password))
        return self._jira

    def findIssues(self, jql):
        fields = [
            'assignee', 'attachment', 'created', 'description', 'fixVersions',
            'summary']
        fields.append('customfield_{}'.format(
            self.jira._get_sprint_field_id()))
        return self.jira.search_issues(jql, fields=', '.join(fields))

    def activeIssues(self):
        jql = 'project={}'.format(self.key)
        jql += ' AND (resolution=Unresolved OR Sprint in openSprints())'
        return self.findIssues(jql)

    def getIssueLastSprint(self, fields):
        """
        Parse Sprints customfield and format it

        Returns:
            jira.resources.Sprint
        """
        if not self._sprintCustomField:
            self._sprintCustomField = 'customfield_{}'.format(
                self.jira._get_sprint_field_id())
        sprints = getattr(fields, self._sprintCustomField)
        if sprints:
            import re
            m = re.search(r'id=(\d+),', sprints[-1])
            id = m.group(1)
            return self.jira.sprint(id)
        return None

    def cp(self):
        issues = self.activeIssues()
        total = len(issues)
        if total == 0:
            logger.info('Nothing to do')
            return self

        i = 0
        for issue in issues:
            try:
                self.project.addIssue(issue)
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

from atlassian2gitlab.gl_resources import Project, ProjectMilestone, User
from atlassian2gitlab.exceptions import A2GException, NotFoundException
import jira
from gitlab import Gitlab
import logging
import requests


__version__ = 0.3


logger = logging.getLogger(__name__)
session = requests.Session()
user_map = {}


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
        """
        Find Gitlab user

        If a user is in the `user_map` dict, his name will be mapped, even if
        it exists in gitlab.
        But if the user is not found, we will try the special user `_default`.
        Otherwise, the gitlab's token owner will be used.
        """
        if name not in self._users:
            try:
                username = user_map.get(name, name)
                user = User(username, self)
                user.get()
                self._users[name] = user
            except NotFoundException:
                username = user_map.get('_default', 'current')
                logging.getLogger(__name__).debug(
                    'Try the {} user instead'.format(username))
                if username == 'current':
                    self.gitlab.auth()
                    username = self.gitlab.user.username
                self._users[name] = User(username, self)
        return self._users[name]

    def findMilestone(self, title):
        """
        Return the expected project milestone

        We get informations from Gitlab only if necessary, the milestone isn't
        created until we call the `save()` method or the `id` property.
        It's created once, if a milestone with the same title exists, it will
        be used.

        Returns:
            atlassian2gitlab.gl_resources.ProjectMilestone
        """
        if title not in self._milestones:
            self._milestones[title] = ProjectMilestone(title, self)
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
    _fields = None
    _jira = None
    storyPoint_map = {
        5: 4,
        8: 5,
        13: 6,
        21: 7,
        34: 8,
        55: 9
    }

    @property
    def jira(self):
        if not self._jira:
            self._jira = jira.JIRA(
                self.url,
                options={'verify': self.ssl_verify},
                basic_auth=(self.username, self.password))
        return self._jira

    def getFieldId(self, name):
        if not self._fields:
            self._fields = self.jira.fields()
        return [f['id'] for f in self._fields if f['name'] == name][0]

    def findIssues(self, jql):
        fields = [
            'assignee', 'attachment', 'created', 'description', 'fixVersions',
            'summary', 'reporter']
        fields.append(self.getFieldId('Sprint'))
        fields.append(self.getFieldId('Story Points'))
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
        sprints = getattr(fields, self.getFieldId('Sprint'))
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

    def mapStoryPoints(self, dict):
        """
        Add story points mapping to the existing map

        Configparser send DEFAULTSECT, so we have to ignore no numerical keys.

        >>> manager = JiraManager(None, None, None, None, None, None, None)
        >>> manager.storyPoint_map[5]
        4
        >>> manager.mapStoryPoints({'7': '4', 'blah': 'blah'})
        >>> manager.storyPoint_map[7]
        4
        >>> 'blah' in manager.storyPoint_map
        False
        """
        for k, v in dict.items():
            if not k.isdigit():
                continue
            key = int(k)
            value = int(v)
            self.storyPoint_map[key] = value

    def getIssueWeight(self, number):
        """
        Return the appropriate issue weight for the given number

        Search the given number in the Fibonaci suite, commonly used by SCRUM
        teams. If the number is not in the convertion map, we use the value as
        is, but limited at 9 (the max issue weight).

        >>> manager = JiraManager(None, None, None, None, None, None, None)
        >>> manager.getIssueWeight(1)
        1
        >>> manager.getIssueWeight(5)
        4
        >>> manager.getIssueWeight(6)
        6
        >>> manager.getIssueWeight(13)
        6
        >>> manager.getIssueWeight(150)
        9

        Returns:
            int
        """
        n = int(number)
        v = self.storyPoint_map.get(n, n)
        return 9 if v > 9 else v

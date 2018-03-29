import atlassian2gitlab as a2g
from . import gl_resources as resources
import logging
from singleton_decorator import singleton


logger = logging.getLogger(__name__)


@singleton
class GitlabManager(object):
    _gitlab = None
    _project = None
    _attachments = {}
    _milestones = {}
    _users = {}

    @property
    def gitlab(self):
        """
        Return the Gitlab client

        Returns:
            atlassian2gitlab.clients.Gitlab
        """
        if not self._gitlab:
            from atlassian2gitlab.clients import Gitlab
            self._gitlab = Gitlab()
        return self._gitlab

    @property
    def project(self):
        """
        Return the targetted project

        Returns:
            atlassian2gitlab.gl_resources.Project
        """
        if not self._project:
            self._project = resources.Project(a2g.gitlab_repo)
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
            from atlassian2gitlab.exceptions import NotFoundException
            try:
                username = a2g.user_map.get(name, name)
                user = resources.User(username)
                user.get()
                self._users[name] = user
            except NotFoundException:
                username = a2g.user_map.get('_default', 'current')
                logger.debug('Try the {} user instead'.format(username))
                if username == 'current':
                    self.gitlab.auth()
                    username = self.gitlab.user.username
                self._users[name] = resources.User(username)
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
            self._milestones[title] = resources.ProjectMilestone(title)
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


@singleton
class JiraManager(object):
    """
    Manage issues
    """
    _fields = None
    _jira = None

    @property
    def jira(self):
        if not self._jira:
            from atlassian2gitlab.clients import Jira
            self._jira = Jira()
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
        jql = 'project={}'.format(a2g.jira_key)
        jql += ' AND (resolution=Unresolved OR Sprint in openSprints())'
        return self.findIssues(jql)

    def cp(self):
        issues = self.activeIssues()
        total = len(issues)
        if total == 0:
            logger.info('Nothing to do')
            return self

        i = 0
        for issue in issues:
            from atlassian2gitlab.exceptions import A2GException
            try:
                gl_mgr = GitlabManager()
                gl_mgr.project.addIssue(issue)
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

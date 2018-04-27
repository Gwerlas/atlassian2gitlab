import atlassian2gitlab as a2g
from . import gl_resources as resources
import logging
from singleton_decorator import singleton


logger = logging.getLogger('atlassian2gitlab')


@singleton
class GitlabManager(object):
    _client = None
    _group = None
    _project = None
    _attachments = {}
    _labels = {}
    _milestones = {}
    _users = {}

    @property
    def gitlab(self):
        """
        Return the Gitlab client

        Returns:
            atlassian2gitlab.clients.Gitlab
        """
        if not self._client:
            from atlassian2gitlab.clients import Gitlab
            self._client = Gitlab()
        return self._client

    @property
    def group(self):
        from atlassian2gitlab.exceptions import NotFoundException
        if not self._group:
            name = a2g.gitlab_repo.split('/')[0]
            for g in self.gitlab.groups.list(search=name):
                if g.path == name:
                    self._group = g
                    break
            if not self._group:
                raise NotFoundException("No such group `{}'".format(name))
        return self._group

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

        Returns:
            atlassian2gitlab.gl_resources.User
        """
        if name not in self._users.keys():
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

    def findBoard(self, name=None):
        from atlassian2gitlab.exceptions import NotFoundException
        if name:
            try:
                for b in self.group.boards.list(all=True):
                    if b.name == name:
                        return b
            except Exception as e:
                logger.debug(str(e))

        boards = self.project.boards.list(all=True)
        if not len(boards):
            parent = self.group if a2g.gitlab_group_level else self.project
            b = parent.boards.create({
                'name': name or 'Developments'})
            logger.debug("Board `%s' created (%d)", b.name, b.id)
            return b
        elif name:
            for b in boards:
                if b.name == name:
                    return b
            else:
                raise NotFoundException("No such board `{}'".format(name))
        else:
            return boards[0]

    def findLabel(self, name):
        """
        Return the expected project label

        Returns:
            atlassian2gitlab.gl_resources.Label
        """
        if name not in self._labels.keys():
            self._labels[name] = resources.Label(name)
        return self._labels[name]

    def findMilestone(self, title):
        """
        Return the expected project milestone

        Returns:
            atlassian2gitlab.gl_resources.ProjectMilestone
        """
        if title not in self._milestones.keys():
            if a2g.gitlab_group_level:
                self._milestones[title] = resources.GroupMilestone(title)
            else:
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
        if id not in self._attachments.keys():
            a = self.project.upload(
                filename='_'.join([attachment.id, attachment.filename]),
                filedata=attachment.get())
            self._attachments[id] = a
        return self._attachments[id]


@singleton
class BitBucketManager(object):
    """
    Manage source code
    """
    _client = None

    @property
    def bitbucket(self):
        if not self._client:
            from atlassian2gitlab.clients import BitBucket
            self._client = BitBucket()
        return self._client

    @property
    def repo(self):
        from atlassian2gitlab.exceptions import NotFoundException
        project, repo = a2g.bitbucket_repo.split('/')
        url = '/projects/{}/repos/{}'.format(project, repo)
        try:
            repo = self.bitbucket.get(url)
        except Exception as e:
            logger.debug(str(e))
            raise NotFoundException("No such BitBucket repo `{}'".format(
                a2g.bitbucket_repo))
        return repo

    def cp(self):
        try:
            links = self.repo.links.clone
        except Exception as e:
            logger.error('Failed: %s', str(e))
            return

        import os
        import shutil
        import tempfile

        source = [l.href for l in links if l.name == 'ssh'][0]
        tmpdir = tempfile.mkdtemp()
        target = GitlabManager().project.ssh_url_to_repo

        cmdz = [
            ['git', 'clone', '--mirror', source, tmpdir],
            ['git', '-C', tmpdir, 'remote', 'set-url', 'origin', target],
            ['git', '-C', tmpdir, 'push', '--mirror']
        ]
        for cmd in cmdz:
            logger.debug("Run shell command: %s", " ".join(cmd))
            try:
                os.system(" ".join(cmd))
            except Exception as e:
                logger.error('Failed: %s', str(e))
        logger.debug("Removing `%s'", tmpdir)
        shutil.rmtree(tmpdir)


@singleton
class JiraManager(object):
    """
    Manage issues
    """
    _fields = None
    _client = None

    @property
    def jira(self):
        if not self._client:
            from atlassian2gitlab.clients import Jira
            self._client = Jira()
        return self._client

    def getFieldId(self, name):
        if not self._fields:
            self._fields = self.jira.fields()
        return [f['id'] for f in self._fields if f['name'] == name][0]

    def findIssues(self, jql):
        fields = [
            'assignee', 'attachment', 'created', 'description', 'fixVersions',
            'summary', 'reporter', 'comment', 'issuetype', 'status',
            'resolution', 'resolutiondate']
        fields.append(self.getFieldId('Sprint'))
        fields.append(self.getFieldId('Story Points'))
        return self.jira.search_issues(jql, fields=', '.join(fields))

    def cp(self):
        issues = self.findIssues(a2g.jira_jql)
        total = len(issues)

        if total == 0:
            logger.info('Nothing to do')
            return self
        else:
            logger.info('%d issues to migrate', total)

        i = 0
        skipped = 0
        for issue in issues:
            if issue.fields.issuetype.name == a2g.jira_epic_type:
                logger.warning("Skip issue %s: It's an Epic", issue.key)
                skipped += 1
                continue
            from atlassian2gitlab.exceptions import A2GException
            try:
                gl_mgr = GitlabManager()
                gl_mgr.project.addIssue(issue)
                i += 1
            except A2GException as e:
                logger.warning('Skip issue %s: %s', issue.key, e)

        if i == (total + skipped):
            logger.info('All done')
        elif i == 0:
            logger.error('Any issues migrated')
        else:
            logger.warn(
                '%d/%d issues migrated (%d skipped)',
                i, total, skipped)

        return self

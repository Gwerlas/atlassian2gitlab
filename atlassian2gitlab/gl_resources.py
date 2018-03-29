import logging
import atlassian2gitlab as a2g
from . import managers
from .exceptions import NotFoundException


class Resource(object):
    _item = None
    toSave = False

    def __init__(self):
        name = '.'.join((self.__module__, self.__class__.__name__))
        self.logger = logging.getLogger(name)

    def __getattr__(self, name):
        return getattr(self.get(), name)

    def create(self):
        raise NotImplementedError

    def get(self):
        raise NotImplementedError

    def save(self):
        """
        Save the resource to Gitlab

        Returns:
            Resource
        """
        if self.toSave:
            self.get().save()
            self.toSave = False
        return self


class Issue(Resource):
    _data = {}

    def __init__(self):
        Resource.__init__(self)
        self.project = managers.GitlabManager().project

    def save(self):
        """
        Create the Gitlab issue (update not yet supported)
        """
        if not self._item:
            self._item = self.project.issues.create(
                self._data,
                sudo=self.owner.username)
            self._data = {}
            self.toSave = False
        return self

    def setData(self, k, v):
        if not hasattr(self._item, k) or getattr(self._item, k) != v:
            self._data[k] = v
            self.toSave = True
        return self

    def setAssignee(self, username):
        assignee = managers.GitlabManager().findUser(username)
        self.setData('assignee_ids', [assignee.id])

    def getSprint(self, fields):
        """
        Parse Sprints customfield and format it

        Returns:
            jira.resources.Sprint
        """
        manager = managers.JiraManager()
        field = manager.getFieldId('Sprint')
        sprints = getattr(fields, field) if hasattr(fields, field) else None
        if sprints:
            import re
            m = re.search(r'id=(\d+),', sprints[-1])
            id = m.group(1)
            return manager.jira.sprint(id)
        return None

    def setMilestoneFromSprint(self, sprint):
        milestone = managers.GitlabManager().findMilestone(str(sprint))
        milestone.fillFromJiraSprint(sprint)
        self.setData('milestone_id', milestone.id)

    def setMilestoneFromVersion(self, version):
        milestone = managers.GitlabManager().findMilestone(str(version))
        milestone.fillFromJiraVersion(version)
        self.setData('milestone_id', milestone.id)

    def getWeight(self, number):
        """
        Return the appropriate issue weight for the given number

        Search the given number in the Fibonaci suite, commonly used by SCRUM
        teams. If the number is not in the convertion map, we use the value as
        is, but limited at 9 (the max issue weight).

        >>> from atlassian2gitlab.managers import GitlabManager
        >>> issue = Issue()
        >>> issue.getWeight(1)
        1
        >>> issue.getWeight(5)
        4
        >>> issue.getWeight(6)
        6
        >>> issue.getWeight(13)
        6
        >>> issue.getWeight(150)
        9

        Returns:
            int
        """
        n = int(number)
        v = a2g.storyPoint_map.get(n, n)
        return 9 if v > 9 else v

    def setWeight(self, number):
        self.setData('weight', self.getWeight(number))

    def setOwner(self, username):
        self.owner = managers.GitlabManager().findUser(username)

    def fillFromJira(self, jira_issue):
        from atlassian2gitlab.at_resources import JiraNotationConverter
        manager = managers.JiraManager()
        fields = jira_issue.fields
        self.setData('created_at', fields.created)
        self.setData('title', fields.summary)

        converter = JiraNotationConverter(jira_issue)

        if fields.reporter:
            self.setOwner(fields.reporter.name)

        if fields.assignee:
            self.setAssignee(fields.assignee.name)

        if fields.description:
            self.setData(
                'description',
                converter.toMarkdown(fields.description))

        sprint = self.getSprint(fields)
        if sprint:
            self.setMilestoneFromSprint(sprint)
        elif len(fields.fixVersions):
            self.setMilestoneFromVersion(fields.fixVersions[-1])

        spField = manager.getFieldId('Story Points')
        if hasattr(fields, spField) and getattr(fields, spField):
            self.setWeight(getattr(fields, spField))
        return self.save()


class Project(Resource):
    _users = {}
    _repo = None

    def __init__(self, repo):
        Resource.__init__(self)
        self._repo = repo

    def get(self):
        """
        Find the project by his name

        Raises:
            NotFoundException

        Returns:
            gitlab.v4.objects.Project
        """
        if not self._item:
            search = self._repo.split('/')[1]
            projects = managers.GitlabManager().gitlab.projects.list(
                search=search)
            for project in projects:
                if project.path_with_namespace == self._repo:
                    self._item = project
                    return project
            raise NotFoundException("Project {} not found".format(self._repo))
        return self._item

    def addIssue(self, jira_issue):
        """
        Create an issue from a Jira issue object

        Args:
            jira.resources.Issue

        Returns:
            atlassian2gitlab.gl_resources.Issue
        """
        issue = Issue()
        issue.fillFromJira(jira_issue)
        return issue

    def flush(self):
        logger = logging.getLogger(__name__)
        issues = self.get().issues.list(all=True)
        milestones = self.get().milestones.list(all=True)
        if len(issues) + len(milestones) == 0:
            logger.info('Nothing to do')
            return self

        if len(issues):
            total = len(issues)
            i = 0
            for issue in issues:
                try:
                    issue.delete()
                    i += 1
                except Exception as e:
                    id = issue.id
                    logger.warn('Issue %s has not been deleted: %s', id, e)

            if i == total:
                logger.info('All %d issues deleted', total)
            elif i == 0:
                logger.error('Any issues deleted')
            else:
                logger.warn('%d/%d issues deleted', i, total)

        if len(milestones):
            total = len(milestones)
            i = 0
            for m in milestones:
                try:
                    m.delete()
                    i += 1
                except Exception as e:
                    logger.warn('Milestone "%s" has not been deleted: %s',
                                m.title, e)

            if i == total:
                logger.info('All %d milestones deleted', total)
            elif i == 0:
                logger.error('Any milestones deleted')
            else:
                logger.warn('%d/%d milestones deleted', i, total)

        return self


class ProjectMilestone(Resource):
    def __init__(self, title):
        Resource.__init__(self)
        self._title = title

    def get(self):
        if not self._item:
            milestones = managers.GitlabManager().project.milestones.list(
                search=self._title)
            for m in milestones:
                if m.title == self._title:
                    self._item = m
                    break
            if not self._item:
                self.create()
        return self._item

    def create(self):
        data = {'title': self._title}
        self._item = managers.GitlabManager().project.milestones.create(data)
        self.logger.debug('Milestone {} created : #{}'.format(
            self._title, self._item.id
        ))
        return self

    def fillFromJiraSprint(self, sprint):
        m = self.get()
        if sprint.endDate and sprint.endDate != m.due_date:
            m.due_date = sprint.endDate
            self.toSave = True
        if sprint.state == 'CLOSED' and m.state == 'active':
            m.state_event = 'close'
            self.toSave = True
        return self.save()

    def fillFromJiraVersion(self, version):
        m = self.get()
        if version.releaseDate and version.releaseDate != m.due_date:
            m.due_date = version.releaseDate
            self.toSave = True
        if version.released and m.state == 'active':
            m.state_event = 'close'
            self.toSave = True
        return self.save()


class User(Resource):
    def __init__(self, username):
        Resource.__init__(self)
        self._username = username

    def get(self):
        """
        Find the user by his name

        Raises:
            NotFoundException

        Returns:
            gitlab.v4.objects.User
        """
        if not self._item:
            users = managers.GitlabManager().gitlab.users.list(
                username=self._username)
            if len(users) == 1:
                self._item = users[0]
            else:
                err = '{} users found matching {}'.format(
                    len(users),
                    self._username)
                logging.getLogger(__name__).debug(
                    "No such user `%s'" % self._username)
                raise NotFoundException(err)
        return self._item

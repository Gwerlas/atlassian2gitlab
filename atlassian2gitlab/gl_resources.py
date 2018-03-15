import logging
from atlassian2gitlab.at_resources import JiraNotationConverter
from atlassian2gitlab.exceptions import NotFoundException


class Resource(object):
    _name = None
    _item = None
    manager = None
    toSave = False

    def __init__(self, name, manager):
        self.logger = logging.getLogger(__name__)
        self.manager = manager
        self._name = name

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


class Project(Resource):
    _users = {}

    def get(self):
        """
        Find the project by his name

        Raises:
            NotFoundException

        Returns:
            gitlab.v4.objects.Project
        """
        if not self._item:
            search = self._name.split('/')[1]
            for project in self.manager.gitlab.projects.list(search=search):
                if project.path_with_namespace == self._name:
                    self._item = project
                    return project
            raise NotFoundException("Project {} not found".format(self._name))
        return self._item

    def addIssue(self, issue):
        """
        Create an issue from a Jira issue object

        Args:
            jira.resources.Issue

        Returns:
            gitlab.v4.objects.Issue
        """
        fields = issue.fields
        data = {
            'created_at': fields.created,
            'title': fields.summary
        }
        converter = JiraNotationConverter(self.manager, issue)
        owner = self.manager.findUser(fields.reporter.name)

        if fields.assignee:
            assignee = self.manager.findUser(fields.assignee.name)
            data['assignee_ids'] = [assignee.id]

        if fields.description:
            data['description'] = converter.toMarkdown(fields.description)

        sprint = self.manager.getIssueLastSprint(fields)
        if sprint:
            milestone = self.manager.findMilestone(str(sprint))
            data['milestone_id'] = milestone.fillFromJiraSprint(sprint).id
        elif len(fields.fixVersions):
            version = fields.fixVersions[-1]
            milestone = self.manager.findMilestone(str(version))
            data['milestone_id'] = milestone.fillFromJiraVersion(version).id

        spField = self.manager.getFieldId('Story Points')
        if hasattr(fields, spField) and getattr(fields, spField):
            sp = getattr(fields, spField)
            data['weight'] = self.manager.getIssueWeight(sp)

        return self.get().issues.create(data, sudo=owner.username)

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
    def get(self):
        if not self._item:
            for m in self.manager.project.milestones.list(search=self._name):
                if m.title == self._name:
                    self._item = m
                    break
            if not self._item:
                self.create()
        return self._item

    def create(self):
        data = {'title': self._name}
        self._item = self.manager.project.milestones.create(data)
        self.logger.debug('Milestone {} created : #{}'.format(
            self._name, self._item.id
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
    def get(self):
        """
        Find the user by his name

        Raises:
            NotFoundException

        Returns:
            gitlab.v4.objects.User
        """
        if not self._item:
            users = self.manager.gitlab.users.list(username=self._name)
            if len(users) == 1:
                self._item = users[0]
            else:
                err = '{} users found matching {}'.format(
                    len(users),
                    self._name)
                logging.getLogger(__name__).debug(
                    "No such user `%s'" % self._name)
                raise NotFoundException(err)
        return self._item

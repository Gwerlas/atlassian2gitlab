import logging
import atlassian2gitlab as a2g
from atlassian2gitlab.exceptions import NotFoundException


class Ressource(object):
    _gl = None
    _name = None
    _item = None

    def __init__(self, name, gitlab):
        self._gl = gitlab
        self._name = name


class Project(Ressource):
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
            for project in self._gl.projects.list(search=search):
                if project.path_with_namespace == self._name:
                    self._item = project
                    return project
            raise NotFoundException("Project {} not found".format(self._name))
        return self._item

    def addIssue(self, fields):
        """
        Create an issue from a Jira issue object

        Returns:
            gitlab.v4.objects.Issue
        """
        data = {
            'created_at': fields.created,
            'title': fields.summary
        }

        if fields.assignee:
            name = a2g.user_map.get(
                fields.assignee.name, fields.assignee.name)
            assignee = User(name, self._gl).get()
            data['assignee_ids'] = [assignee.id]

        return self.get().issues.create(data)

    def flush(self):
        logger = logging.getLogger(__name__)
        issues = self.get().issues.list(all=True)
        total = len(issues)
        if total == 0:
            logger.info('Nothing to do')
            return self

        i = 0
        for issue in issues:
            try:
                issue.delete()
                i += 1
            except Exception as e:
                logger.warn('Issue %s has not been deleted: %s', issue.id, e)

        if i == total:
            logger.info('All %d issues deleted', total)
        elif i == 0:
            logger.error('Any issues deleted')
        else:
            logger.warn('%d/%d issues deleted', i, total)
        return self


class User(Ressource):
    def get(self):
        """
        Find the user by his name

        Raises:
            NotFoundException

        Returns:
            gitlab.v4.objects.User
        """
        if not self._item:
            users = self._gl.users.list(username=self._name)
            if len(users) == 1:
                self._item = users[0]
            else:
                err = '{} users matching {} found'.format(len(users),
                                                          self._name)
                raise NotFoundException(err)
        return self._item

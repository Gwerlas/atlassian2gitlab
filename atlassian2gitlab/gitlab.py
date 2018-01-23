import gitlab
import logging


class Gitlab(gitlab.Gitlab):
    """Extension of python-gilatb for our usage"""
    _users = {}

    def search_project_from_repo(self, repo):
        """
        Find the project by his name

        Raises:
            Exception: Not found

        Returns:
            gitlab.v4.objects.Project
        """
        search = repo.split('/')[1]
        projects = self.projects.list(search=search)
        for project in projects:
            if project.path_with_namespace == repo:
                return project
        raise Exception("Project {} not found".format(repo))

    def get_user_by_name(self, name):
        """
        Find the user by his name

        Raises:
            Exception: Not found

        Returns:
            gitlab.v4.objects.User
        """
        if name in self._users:
            return self._users[name]

        users = self.users.list(username=name)
        if len(users) == 1:
            self._users[name] = users[0]
            return users[0]

        raise Exception('{} users matching {} found'.format(len(users), name))

    def create_from_jira(self, project, issue):
        """
        Create an issue from a Jira issue object

        Returns:
            gitlab.v4.objects.Issue
        """
        data = {
            'title': issue.fields.summary
        }

        if issue.fields.assignee:
            assignee = self.get_user_by_name(issue.fields.assignee.name)
            data['assignee_ids'] = [assignee.id]

        return project.issues.create(data)

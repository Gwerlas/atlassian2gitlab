import gitlab


class Gitlab(gitlab.Gitlab):
    """Extension of python-gilatb for our usage"""

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

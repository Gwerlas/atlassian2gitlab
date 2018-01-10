import requests


class Gitlab(object):
    """Gitlab connector"""
    projectId = None

    def __init__(self, url, repo, token):
        self.url = url
        self.repo = repo
        self.token = token

    def getProjectId(self):
        """
        Resolve the project ID

        Search it by repo name, and filter on the full namespace

        :raise Exception: Project not found

        :return: int Project id
        """
        if not self.projectId:
            print(self.repo.split('/'))
            namespace, repo = self.repo.split('/')
            projects = requests.get(
                '{url}api/v4/projects?search={repo}'.format(
                    url=self.url,
                    repo=repo),
                headers={'PRIVATE-TOKEN': self.token}).json()
            for project in projects:
                if project['path_with_namespace'] == self.repo:
                    self.projectId = project['id']
                    break

            if not self.projectId:
                raise Exception("Project {} not found".format(self.repo))

            self.projectId = project['id']

        return self.projectId

    def addIssue(self, data):
        return requests.post(
            '{url}api/v4/projects/{project}/issues'.format(
                url=self.url,
                project=self.getProjectId()),
            headers={'PRIVATE-TOKEN': self.token},
            data=data)

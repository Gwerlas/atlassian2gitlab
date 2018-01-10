from atlassian2gitlab.atlassian import Atlassian


class Jira(Atlassian):
    """Jira connector"""
    limit = 10000

    def __init__(self, username, password, jira_url, project_key):
        Atlassian.__init__(self, username, password)
        self.url = jira_url
        self.project = project_key

    def get(self, jql):
        """
        Sends a get request to Jira

        :param jql: The URL encoded JQL string

        :return: requests.Response
        """
        import requests
        r = requests.get(
            '{url}rest/api/2/search?jql={jql}'.format(url=self.url, jql=jql),
            auth=(self.username, self.password),
            headers={'Content-Type': 'application/json'})
        r.raise_for_status()
        return r

    def getIssues(self, jql):
        """
        Get issues from Jira

        :param jql: The URL encoded JQL string

        :return: The issue list.
        """
        return self.get(jql).json()['issues']

    def getActiveIssues(self):
        """
        Get Jira issues from Backlog and in active sprints

        Fetch issues from the current Jira project where the status is
        unresolved or in active sprints.
        The most usefull to migrate from Jira, keeping the to do list and the
        sprint progress bar.

        :return: The issue list.
        """
        return self.getIssues(
            'project={key}'.format(key=self.project) +
            '+AND+(resolution=Unresolved+OR+Sprint+in+openSprints())' +
            '+ORDER+BY+createdDate+ASC&maxResults={:d}'.format(self.limit))

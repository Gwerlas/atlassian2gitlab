from jira import JIRA


class Jira(JIRA):
    """Extension of jira-python for our usage"""

    def active_issues(self, project):
        jql = 'project={}'.format(project)
        jql += ' AND (resolution=Unresolved OR Sprint in openSprints())'
        return self.search_issues(jql)

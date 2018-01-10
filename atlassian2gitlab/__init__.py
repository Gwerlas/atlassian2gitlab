from atlassian2gitlab.options import Options
from atlassian2gitlab.jira import Jira
from atlassian2gitlab.gitlab import Gitlab


def migrate():
    args = Options().values
    jira = Jira(
        args.AT_USER,
        args.AT_PASS,
        args.JIRA_URL,
        args.JIRA_PROJECT_KEY)
    gitlab = Gitlab(
        args.GL_URL,
        args.GL_REPO,
        args.GL_TOKEN)

    for issue in jira.getActiveIssues():
        print(gitlab.addIssue({
            'title': issue['fields']['summary']
        }))

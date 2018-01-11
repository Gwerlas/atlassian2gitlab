from atlassian2gitlab.jira import Jira
from atlassian2gitlab.gitlab import Gitlab


gitlab_api_version = 4
gitlab_repo = None
gitlab_token = None
gitlab_url = None
jira_project_key = None
jira_url = None
atlassian_user = None
atlassian_pass = None
ssl_verify = True


def issues():
    gitlab = Gitlab(gitlab_url, private_token=gitlab_token,
                    api_version=4, ssl_verify=ssl_verify)
    jira = Jira(jira_url, basic_auth=(atlassian_user, atlassian_pass),
                options={'verify': ssl_verify})

    project = gitlab.search_project_from_repo(gitlab_repo)

    for issue in jira.active_issues(jira_project_key):
        print(project.issues.create({
            'title': issue.fields.summary
        }))

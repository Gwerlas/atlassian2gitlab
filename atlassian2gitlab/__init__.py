from atlassian2gitlab.jira import Jira
from atlassian2gitlab.gitlab import Gitlab
import logging


debug = False
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
    logger = logging.getLogger(__name__)
    if not ssl_verify:
        logger.warn('You disabled SSL checks, it is not recommanded !')

    gitlab = Gitlab(gitlab_url, private_token=gitlab_token,
                    api_version=4, ssl_verify=ssl_verify)
    jira = Jira(jira_url, basic_auth=(atlassian_user, atlassian_pass),
                options={'verify': ssl_verify})

    if debug:
        gitlab.enable_debug()

    project = gitlab.search_project_from_repo(gitlab_repo)
    issues = jira.active_issues(jira_project_key)

    i = 0
    for issue in issues:
        try:
            gitlab.create_from_jira(project, issue)
            i += 1
        except Exception as e:
            logger.warning('Skip issue {}: {}'.format(issue, e))

    total = len(issues)
    if i == total:
        logger.info('All {} issues migrated'.format(total))
    elif i == 0:
        logger.error('Any issues migrated')
    else:
        logger.warn('{}/{} issues migrated'.format(i, len(issues)))


def flush():
    logger = logging.getLogger(__name__)
    if not ssl_verify:
        logger.warn('You disabled SSL checks, it is not recommanded !')

    gitlab = Gitlab(gitlab_url, private_token=gitlab_token,
                    api_version=4, ssl_verify=ssl_verify)

    if debug:
        gitlab.enable_debug()

    project = gitlab.search_project_from_repo(gitlab_repo)
    issues = project.issues.list(all=True)

    logger.info('{} issues to delete'.format(len(issues)))
    i = 0
    for issue in issues:
        issue.delete()
        logger.debug('Issue {} deleted'.format(issue.id))
        i += 1

    logger.info('{} issues deleted'.format(i))

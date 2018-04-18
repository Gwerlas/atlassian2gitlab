import atlassian2gitlab as a2g
import requests
from munch import munchify


session = requests.Session()


class Gitlab(object):
    __gitlab = None

    def __getattr__(self, name):
        if not self.__gitlab:
            import gitlab
            self.__gitlab = gitlab.Gitlab(
                a2g.gitlab_url,
                private_token=a2g.gitlab_token,
                ssl_verify=a2g.ssl_verify,
                api_version=4,
                session=session)
        return getattr(self.__gitlab, name)


class BitBucket(object):
    def __init__(self):
        if a2g.bitbucket_url == 'https://bitbucket.org':
            self.api_url = 'https://api.bitbucket.org/1.0'
        else:
            self.api_url = '{}/rest/api/1.0'.format(a2g.bitbucket_url)

    def get(self, url):
        r = requests.get(
            self.api_url + url,
            auth=(a2g.bitbucket_username, a2g.bitbucket_password),
            headers={'Content-Type': 'application/json'})
        r.raise_for_status()
        return munchify(r.json())


class Jira(object):
    __jira = None

    def __getattr__(self, name):
        if not self.__jira:
            import jira
            self.__jira = jira.JIRA(
                a2g.jira_url,
                options={'verify': a2g.ssl_verify},
                basic_auth=(a2g.jira_username, a2g.jira_password))
        return getattr(self.__jira, name)

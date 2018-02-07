Migrate from the Atlassian suite to Gitlab
==========================================

[![pipeline status](https://gitlab.com/gwerlas/atlassian2gitlab/badges/master/pipeline.svg)](https://gitlab.com/gwerlas/atlassian2gitlab/commits/master)
[![coverage report](https://gitlab.com/gwerlas/atlassian2gitlab/badges/master/coverage.svg)](https://gitlab.com/gwerlas/atlassian2gitlab/commits/master)

Introduction
------------

This project is very young, the *future* first version will only support issue migration from Jira to Gitlab.

Based on [`python-gitlab`](https://pypi.python.org/pypi/python-gitlab) and [`jira`](https://pypi.python.org/pypi/jira) Python modules.

Installation
------------

Supported version of python :

* 2.7
* 3.4
* 3.5
* 3.6
* Pypy
* Pypy3

Usage
-----

```bash
$ atlassian2gitlab [-h] [--gitlab-url GL_URL] --gitlab-token GL_TOKEN
                        --gitlab-repo GL_REPO [--ssl-no-verify] [--debug]
                        [--version] --atlassian-username AT_USER
                        --atlassian-password AT_PASS [--jira-url JIRA_URL]
                        --jira-project-key JIRA_PROJECT_KEY

Migrate from the Atlassian suite to Gitlab

optional arguments:
  -h, --help            show this help message and exit
  --gitlab-url GL_URL   Gitlab URL (default: https://gitlab.com/)
  --gitlab-token GL_TOKEN
                        Access Token for Gitlab (default: None)
  --gitlab-repo GL_REPO
                        Gitlab project name (default: None)
  --ssl-no-verify       Do not verify SSL certificate (not recommanded)
                        (default: False)
  --debug               Display debug messages (default: False)
  --version             Show version and exit
  --atlassian-username AT_USER
                        Atlassian user name (default: None)
  --atlassian-password AT_PASS
                        Atlassian password (default: None)
  --jira-url JIRA_URL   Jira URL (default: https://jira.atlassian.com)
  --jira-project-key JIRA_PROJECT_KEY
                        Jira Project Key (default: None)
```

If You need to empty your GitLab project before :

```bash
$ flush-gitlab [-h] [--gitlab-url GL_URL] --gitlab-token GL_TOKEN
                    --gitlab-repo GL_REPO [--ssl-no-verify] [--debug]
                    [--version]

Flush your Gitlab

optional arguments:
  -h, --help            show this help message and exit
  --gitlab-url GL_URL   Gitlab URL (default: https://gitlab.com/)
  --gitlab-token GL_TOKEN
                        Access Token for Gitlab (default: None)
  --gitlab-repo GL_REPO
                        Gitlab project name (default: None)
  --ssl-no-verify       Do not verify SSL certificate (not recommanded)
                        (default: False)
  --debug               Display debug messages (default: False)
  --version             Show version and exit
```

## Contributing

Install Python, PIP and Tox. Run Tox to check your environment.

If You want to install dependencies and run tests manually :

```bash
pip install -r requirements.txt
pip install munch pytest-cov pytest-mock
pip install -e .
pytest --cov=atlassian2gitlab

# With coverage in HTML format
pytest --cov=atlassian2gitlab --cov-report=html:../coverage
```

It is recommended to use PIP to install dependencies, your distribution may not have the appropriate/latest version of them.

> If you are a Gentoo user :
>
> You should add the `--user` argument on `pip install` calls.

To test your code, you can use https://pycontribs.atlassian.net.
# Migrate from the Atlassian suite to Gitlab

[![pipeline status](https://gitlab.com/gwerlas/atlassian2gitlab/badges/master/pipeline.svg)](https://gitlab.com/gwerlas/atlassian2gitlab/commits/master)
[![coverage report](https://gitlab.com/gwerlas/atlassian2gitlab/badges/master/coverage.svg)](https://gitlab.com/gwerlas/atlassian2gitlab/commits/master)

## Introduction

This project is very young, the _future_ first version will only support issue
migration from Jira to Gitlab.

## Installation

Supported version of python :
 * 3.4
 * 3.5
 * 3.6
 * Pypy3

I do not support Python 2 cause of import troubles :  
I use `jira` python module extended in `jira.py`. There is no troubles with
Python 3, but Python 2 raise an `ImportError` and I have chosen to not support Python 2.

If someone want to solve it, he is welcome !

## Usage

```
$ atlassian2gitlab [-h] [--gitlab-url GL_URL] --gitlab-token GL_TOKEN
                        --gitlab-repo GL_REPO --atlassian-username AT_USER
                        --atlassian-password AT_PASS [--jira-url JIRA_URL]
                        --jira-project-key JIRA_PROJECT_KEY [--ssl-no-verify]
                        [--debug]

Migrate from the Atlassian suite to Gitlab.

optional arguments:
  -h, --help            show this help message and exit
  --gitlab-url GL_URL   Gitlab URL (default: https://gitlab.com/)
  --gitlab-token GL_TOKEN
                        Access Token for Gitlab (default: None)
  --gitlab-repo GL_REPO
                        Gitlab project name (default: None)
  --atlassian-username AT_USER
                        Atlassian user name (default: None)
  --atlassian-password AT_PASS
                        Atlassian password (default: None)
  --jira-url JIRA_URL   Jira URL (default: https://jira.atlassian.com)
  --jira-project-key JIRA_PROJECT_KEY
                        Jira Project Key (default: None)
  --ssl-no-verify       Do not verify SSL certificate (not recommanded)
                        (default: False)
  --debug               Display debug messages (default: False)
```

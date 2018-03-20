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
* Pypy3

Usage
-----

```bash
usage: atlassian2gitlab [-h] -c CONFIG [-d] [-V]

Migrate from the Atlassian suite to Gitlab

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Config file path
  -d, --debug           Display debug messages
  -V, --version         Show version and exit
```

If You need to empty your GitLab project before :

```bash
usage: flush-gitlab [-h] -c CONFIG [-d] [-V]

Flush your Gitlab

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Config file path
  -d, --debug           Display debug messages
  -V, --version         Show version and exit
```

I recommand to copy and edit the `config-sample.ini` from the project sources.

Here is an example of config file :

```ini
[DEFAULT]
; Disable SSL checks globally (not recommanded)
;ssl_verify = False

; Generic Atlassian credentials (not used by GitLab)
username = john.doe@domain.tld
password = very-secret

[gitlab]
url = http://your-gitlab-url.tld/
token = get-this-token-from-your-profile
repo = namespaced/project/name

[jira]
url = https://pycontribs.atlassian.net
key = Z3E79A974A
```

### User mapping

You can map user names between the two platforms adding a `user_map` section to the configuration file :

```ini
[user_map]
_default = admin.user
elan.ruusamae = john.doe
```

If a user is in the `user_map` section, his name will be mapped, even if it exists in gitlab.
But if the user is not found, we will try the special user `_default`.
Otherwise, the gitlab's token owner will be used.

### Issue weight

You can convert Jira story points to Gitlab issue weight using a `story_points` section in the config file.  


```ini
[story_points]
; Jira => Gitlab
20 = 7
40 = 8
100 = 9
```

By default, we convert from the Fibonaci suite, commonly used by SCRUM teams, to Gitlab issue weight :

| Story points (Jira) | Issue weight (Gitlab) |
| ------------------- | --------------------- |
|          1          |           1           |
|          2          |           2           |
|          3          |           3           |
|          5          |           4           |
|          8          |           5           |
|         13          |           6           |
|         21          |           7           |
|         34          |           8           |
|         55          |           9           |

If the story points value is nor in this table, nor in the config file map, we use the value as is, but limited at 9 (the max issue weight).

Contributing
------------

Install Python, PIP and Tox. Run Tox to check your environment.

If You want to install dependencies and run tests manually :

```bash
pip install -r requirements.txt
pip install munch pytest-cov pytest-mock pytest-datadir-ng
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

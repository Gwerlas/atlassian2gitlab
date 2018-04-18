Migrate from the Atlassian suite to Gitlab
==========================================

[![pipeline status](https://gitlab.com/gwerlas/atlassian2gitlab/badges/master/pipeline.svg)](https://gitlab.com/gwerlas/atlassian2gitlab/commits/master)
[![coverage report](https://gitlab.com/gwerlas/atlassian2gitlab/badges/master/coverage.svg)](https://gitlab.com/gwerlas/atlassian2gitlab/commits/master)

Introduction
------------

This project is still quite young, the goal is to migrate from Confluence, Jira, Bitbucket and Bamboo to Gitlab.

State of developments :

- [ ] Confluence
- [X] Jira
- [X] Bitbucket
- [ ] Bamboo

### Requirements

You need to create the project, users and roles in Gitlab first.

If You migrate the Git repository, You need to have Git installed and resolvable from the environment `PATH`.  
Your SSH public key has to be present in your Bitbucket account.

### Features

What is currently supported :

* Git repository, with :
  * Branches
  * Tags
* Issues, with :
  * Creation date
  * Title
  * Assignee
  * Description (translated from atlassian notation to markdown)
  * Jira versions or sprints as milestone
  * Story points as weight
  * Jira issue types as label
  * Jira issue status as label
  * Comments, with:
    * Creation date
    * Author
    * Content (translated from atlassian notation to markdown)
  * A link to the Jira issue as comment (feature flipped)
* Issue boards
* Label (with color)

Based on [`python-gitlab`](https://pypi.python.org/pypi/python-gitlab) and [`jira`](https://pypi.python.org/pypi/jira) Python modules.

Installation
------------

Supported versions of python :

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

### Outputs and logs

There is neither verbose nor debugging options because everything is configurable. Here is a simple example to have basics outputs :

```ini
[loggers]
keys = root,atlassian2gitlab

[logger_root]
handlers = 
level = INFO

[logger_atlassian2gitlab]
handlers = stream
level = NOTSET
qualname = atlassian2gitlab

[handlers]
keys = stream

[handler_stream]
class = StreamHandler
level = NOTSET
formatter = color
args = ()

[formatters]
keys = color

[formatter_color]
class = colorlog.ColoredFormatter
format = %(log_color)s%(message)s
```

You can find a more complete example in the [config-sample.ini](config-sample.ini) file.

Also, You can look at the [Configuration file format](https://docs.python.org/3/library/logging.config.html#configuration-file-format) documentation for more facilities.

### Links between Atlassian and Gitlab

By default, we add a Link to the source. It's usefull while transitting from Atlassian to Gitlab.  
You can turn off this feature in the config file. For example, turning off link creation to Jira :

```ini
[jira]
link_to_source = Off
```

Or globally for the entire Atlassian suite :

```ini
[DEFAULT]
link_to_source = Off
```

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

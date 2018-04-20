import logging
from dateutil.parser import parse
import atlassian2gitlab as a2g
from . import managers
from .exceptions import NotFoundException
from gitlab.exceptions import GitlabGetError


logger = logging.getLogger('atlassian2gitlab')


class Issue(object):
    def __init__(self):
        self._item = None
        self._owner = None
        self.assignee_ids = []
        self.created_at = None
        self.description = None
        self.labels = []
        self.milestone_id = None
        self.title = None
        self.weight = 0

    def save(self):
        """
        Create the Gitlab issue (update not yet supported)
        """
        project = managers.GitlabManager().project
        self._item = project.issues.create({
            'created_at': self.created_at,
            'title': self.title,
            'assignee_ids': self.assignee_ids,
            'description': self.description,
            'milestone_id': self.milestone_id,
            'weight': self.weight,
            'labels': self.labels},
            sudo=self._owner)
        logger.debug("Issue `{}' created (#{})".format(
            self.title, self._item.iid))

    def getSprint(self, fields):
        """
        Parse Sprints customfield and format it

        Returns:
            jira.resources.Sprint
        """
        manager = managers.JiraManager()
        field = manager.getFieldId('Sprint')
        sprints = getattr(fields, field) if hasattr(fields, field) else None
        if sprints:
            import re
            m = re.search(r'id=(\d+),', sprints[-1])
            id = m.group(1)
            return manager.jira.sprint(id)

    def getDominantColorFromUrl(self, url):
        import os
        import urllib.request
        from colorthief import ColorThief
        tmpfile, headers = urllib.request.urlretrieve(url)
        if headers.get_content_type() == 'image/svg+xml':
            from svglib.svglib import svg2rlg
            from reportlab.graphics import renderPM
            drawing = svg2rlg(tmpfile)
            renderPM.drawToFile(drawing, tmpfile)
        color = ColorThief(tmpfile).get_color(quality=1)
        os.unlink(tmpfile)
        return '#%02x%02x%02x' % color

    def addLabel(self, name, colorname=None, iconUrl=None):
        label = managers.GitlabManager().findLabel(name)
        if not label.color:
            if colorname:
                import webcolors
                label.color = webcolors.name_to_hex(colorname)
            elif iconUrl:
                label.color = self.getDominantColorFromUrl(iconUrl)
            if label.color:
                label.save()
        if name not in self.labels:
            self.labels.append(name)
        return label

    def addLabelFromIssueType(self, issuetype):
        self.addLabel(issuetype.name, iconUrl=issuetype.iconUrl)

    def addLabelFromStatus(self, status):
        if status.raw['statusCategory']['key'] not in ('new', 'done'):
            name = status.name
            colorname = status.raw['statusCategory']['colorName'].split('-')[0]
            label = self.addLabel(name, colorname=colorname)
            board = managers.GitlabManager().findBoard()
            if not [l.label['name'] for l in board.lists.list()].count(name):
                board.lists.create({'label_id': label.id})
                logger.debug("Add label `%s' to the board", name)

    def setMilestoneFromSprint(self, sprint):
        milestone = managers.GitlabManager().findMilestone(str(sprint))
        milestone.fillFromJiraSprint(sprint)
        self.milestone_id = milestone.id

    def setMilestoneFromVersion(self, version):
        milestone = managers.GitlabManager().findMilestone(str(version))
        milestone.fillFromJiraVersion(version)
        self.milestone_id = milestone.id

    def getWeight(self, number):
        """
        Return the appropriate issue weight for the given number

        Search the given number in the Fibonaci suite, commonly used by SCRUM
        teams. If the number is not in the convertion map, we use the value as
        is, but limited at 9 (the max issue weight).

        >>> from atlassian2gitlab.managers import GitlabManager
        >>> issue = Issue()
        >>> issue.getWeight(1)
        1
        >>> issue.getWeight(5)
        4
        >>> issue.getWeight(6)
        6
        >>> issue.getWeight(13)
        6
        >>> issue.getWeight(150)
        9

        Returns:
            int
        """
        n = int(number)
        v = a2g.storyPoint_map.get(n, n)
        return 9 if v > 9 else v

    def fillFromJira(self, jira_issue):
        from atlassian2gitlab.at_resources import JiraNotationConverter
        converter = JiraNotationConverter(jira_issue)
        jira_manager = managers.JiraManager()
        gl_manager = managers.GitlabManager()
        fields = jira_issue.fields

        self.created_at = parse(fields.created).isoformat()
        self.title = fields.summary

        if fields.reporter:
            self._owner = gl_manager.findUser(fields.reporter.name).username

        if fields.assignee:
            assignee = gl_manager.findUser(fields.assignee.name)
            self.assignee_ids = [assignee.id]

        if fields.description:
            self.description = converter.toMarkdown(fields.description)

        sprint = self.getSprint(fields)
        if sprint:
            self.setMilestoneFromSprint(sprint)
        elif len(fields.fixVersions):
            self.setMilestoneFromVersion(fields.fixVersions[-1])

        spField = jira_manager.getFieldId('Story Points')
        if hasattr(fields, spField) and getattr(fields, spField):
            self.weight = self.getWeight(getattr(fields, spField))

        self.addLabelFromIssueType(fields.issuetype)
        if not fields.resolution:
            self.addLabelFromStatus(fields.status)
        self.save()

        if hasattr(fields, 'comment'):
            for comment in fields.comment.comments:
                data = {
                    'body': converter.toMarkdown(comment.body),
                    'created_at': parse(comment.created).isoformat()}
                user = gl_manager.findUser(comment.author.key)
                self._item.notes.create(data, sudo=user.username)

        if a2g.jira_link_to_source:
            key = jira_issue.key
            url = jira_issue.permalink()
            self._item.notes.create({
                'body': 'Imported from [{}]({})'.format(key, url)})

        if fields.resolution:
            self._item.state_event = 'close'
            self._item.updated_at = parse(fields.resolutiondate).isoformat()
            self._item.save()
            logger.debug("Close issue #%d", self._item.iid)


class Label(object):
    _item = None

    def __init__(self, name):
        self.name = name
        self.color = None
        try:
            self._item = managers.GitlabManager().project.labels.get(name)
            self.color = self._item.color
        except GitlabGetError:
            pass

    @property
    def id(self):
        return self._item.id

    def save(self):
        if not self._item:
            self._item = managers.GitlabManager().project.labels.create({
                'name': self.name, 'color': self.color})
            logger.debug("Label `{}' created with `{}' color".format(
                self.name, self.color))
        else:
            self._item.color = self.color
            self._item.save()
            logger.debug("Label `{}' updated with `{}' color".format(
                self.name, self.color))


class Project(object):
    _item = None
    _repo = None

    def __init__(self, repo):
        self._repo = repo
        search = self._repo.split('/')[1]
        projects = managers.GitlabManager().gitlab.projects.list(
            search=search)
        for project in projects:
            if project.path_with_namespace == self._repo:
                self._item = project
                break
        if not self._item:
            raise NotFoundException("Project {} not found".format(self._repo))

    def __getattr__(self, name):
        return getattr(self._item, name)

    def addIssue(self, jira_issue):
        """
        Create an issue from a Jira issue object

        Args:
            jira.resources.Issue

        Returns:
            atlassian2gitlab.gl_resources.Issue
        """
        issue = Issue()
        issue.fillFromJira(jira_issue)
        return issue

    def flush(self):
        tags = self._item.tags.list(all=True)
        branches = self._item.branches.list(all=True)
        issues = self._item.issues.list(all=True)
        labels = self._item.labels.list(all=True)
        milestones = self._item.milestones.list(all=True)

        git_items = len(tags) + len(branches)
        iss_items = len(issues) + len(milestones) + len(labels)
        if git_items + iss_items == 0:
            logger.info('Nothing to do')
            return self

        if len(issues):
            total = len(issues)
            logger.info('%d issues to be deleted', total)
            i = 0
            for issue in issues:
                try:
                    issue.delete()
                    i += 1
                except Exception as e:
                    logger.warn("Issue `%s' has not been deleted: %s",
                                issue.id, e)

            if i == total:
                logger.info('Done')
            elif i == 0:
                logger.error('Any issues deleted')
            else:
                logger.warn('%d/%d issues deleted', i, total)

        if len(labels):
            total = len(labels)
            logger.info('%d labels to be deleted', total)
            i = 0
            for l in labels:
                try:
                    l.delete()
                    i += 1
                except Exception as e:
                    logger.warn("Label `%s' has not been deleted: %s",
                                l.name, e)

            if i == total:
                logger.info('Done')
            elif i == 0:
                logger.error('Any labels deleted')
            else:
                logger.warn('%d/%d labels deleted', i, total)

        if len(milestones):
            total = len(milestones)
            logger.info('%d milestones to be deleted', total)
            i = 0
            for m in milestones:
                try:
                    m.delete()
                    i += 1
                except Exception as e:
                    logger.warn("Milestone `%s' has not been deleted: %s",
                                m.title, e)

            if i == total:
                logger.info('Done')
            elif i == 0:
                logger.error('Any milestones deleted')
            else:
                logger.warn('%d/%d milestones deleted', i, total)

        if len(tags):
            total = len(tags)
            logger.info('%d tags to be deleted', total)
            i = 0
            for t in tags:
                try:
                    t.delete()
                    i += 1
                except Exception as e:
                    logger.warn("Tag `%s' has not been deleted: %s",
                                t.name, e)

            if i == total:
                logger.info('Done')
            elif i == 0:
                logger.error('Any tags deleted')
            else:
                logger.warn('%d/%d tags deleted', i, total)

        if len(branches):
            total = len(branches)
            logger.info('%d branches to be deleted', total)
            i = 0
            for b in branches:
                if b.name == self._item.default_branch:
                    logger.warn("Skip the default branch `%s'", b.name)
                    i += 1
                    continue
                try:
                    b.delete()
                    i += 1
                except Exception as e:
                    logger.warn("Branch `%s' has not been deleted: %s",
                                b.name, e)

            if i == total:
                logger.info('Done')
            elif i == 0:
                logger.error('Any branches deleted')
            else:
                logger.warn('%d/%d branches deleted', i, total)


class Milestone(object):
    _item = None

    def __init__(self, title, parent):
        self.title = title
        for m in parent.milestones.list(search=title):
            if m.title == title:
                self._item = m
                break
        if not self._item:
            self._item = parent.milestones.create({'title': title})
            logger.debug("Milestone `%s' created", title)

    def __getattr__(self, name):
        return getattr(self._item, name)

    def _fill(self, state, due_date=None):
        toSave = False
        if state == 'closed' and self._item.state == 'active':
            self._item.state_event = 'close'
            toSave = True
        if due_date:
            due_date = parse(due_date).strftime('%Y-%m-%d')
            if due_date != self._item.due_date:
                self._item.due_date = due_date
                toSave = True
        if toSave:
            self._item.save()
            logger.debug("Milestone `{}' updated".format(self.title))

    def fillFromJiraSprint(self, sprint):
        state = 'closed' if sprint.state == 'CLOSED' else 'active'
        self._fill(state, sprint.endDate)

    def fillFromJiraVersion(self, version):
        state = 'closed' if version.released else 'active'
        self._fill(state, version.releaseDate)


class GroupMilestone(Milestone):
    def __init__(self, title):
        parent = managers.GitlabManager().group
        Milestone.__init__(self, title, parent)


class ProjectMilestone(Milestone):
    def __init__(self, title):
        parent = managers.GitlabManager().project
        Milestone.__init__(self, title, parent)


class User(object):
    _item = None

    def __init__(self, username):
        self.username = username

    def __getattr__(self, name):
        return getattr(self._item, name)

    def get(self):
        """
        Find the user by his name

        Raises:
            NotFoundException

        Returns:
            gitlab.v4.objects.User
        """
        if not self._item:
            users = managers.GitlabManager().gitlab.users.list(
                username=self.username)
            if len(users) == 1:
                self._item = users[0]
            else:
                err = '{} users found matching {}'.format(
                    len(users),
                    self.username)
                logging.getLogger('atlassian2gitlab').debug(
                    "No such user `%s'" % self.username)
                raise NotFoundException(err)
        return self._item

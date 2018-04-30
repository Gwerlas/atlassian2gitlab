from . import managers
import re


class AtlassianNotationConverter(object):
    _attachments = []
    _forLater = {}

    def _attachmentsToMarkdown(self, match):
        """
        Upload attachment and return the Markdown link

        Returns:
            str
        """
        for a in self._attachments:
            if a.filename == match.group(1):
                return managers.GitlabManager().attachFile(a)['markdown']
        return ''

    def _headingsToMarkdown(self, match):
        return '#' * int(match.group(1)) + ' ' + match.group(2) + '\n'

    def _linksToMarkdown(self, match):
        m = re.match('~', match.group(1))
        if m:
            user = managers.GitlabManager().findUser(match.group(1)[1:])
            return '@{}'.format(user.username)
        m = re.match(r'^(.*?)\|([a-z]+?://.*?)$', match.group(1))
        if m:
            return m.expand(r'[\1](\2)')
        m = re.search('mailto:(.*)$', match.group(1))
        if m:
            return '[{0}](mailto:{0})'.format(m.group(1))
        else:
            return match.group(1)

    def _listsToMarkdown(self, match):
        """
        Translate lists from Atlassian notation to Markdown

        >>> converter = AtlassianNotationConverter()
        >>> match = re.match(r'^([\\*\\#]+) ', '* ')
        >>> converter._listsToMarkdown(match)
        '\\n- '
        >>> match = re.match(r'^([\\*\\#]+) ', '** ')
        >>> converter._listsToMarkdown(match)
        '   - '
        >>> match = re.match(r'^([\\*\\#]+) ', '*#* ')
        >>> converter._listsToMarkdown(match)
        '      - '
        >>> match = re.match(r'^([\\*\\#]+) ', '# ')
        >>> converter._listsToMarkdown(match)
        '\\n1. '
        >>> match = re.match(r'^([\\*\\#]+) ', '*# ')
        >>> converter._listsToMarkdown(match)
        '   1. '
        >>> match = re.match(r'^([\\*\\#]+) ', '**# ')
        >>> converter._listsToMarkdown(match)
        '      1. '
        """
        notation = match.group(1)
        count = len(notation)
        res = '\n' if count == 1 else ''
        res += '   ' * (count - 1)
        res += '1. ' if notation.endswith('#') else '- '
        return res

    def _quotesToMarkdown(self, match):
        """
        Translate lists from Atlassian notation to Markdown

        >>> converter = AtlassianNotationConverter()
        >>> match = re.match(r'(.*)', 'blah', flags=re.DOTALL)
        >>> converter._quotesToMarkdown(match)
        '\\n> blah'
        >>> match = re.match(r'(.*)', 'blah\\nblah', flags=re.DOTALL)
        >>> converter._quotesToMarkdown(match)
        '\\n> blah\\n> blah'
        """
        return '\n' + re.sub(r'^', r'> ', match.group(1), flags=re.MULTILINE)

    def _tableHeadingsToMarkdown(self, match):
        first = '\n\n|'
        second = '|'
        for m in re.finditer(r'(?<=\|\|)([^|]*)(?=\|\|)', match.string):
            first += m.group(1) + '|'
            second += '-' * len(m.group(1)) + '|'
        return first + '\n' + second

    def toMarkdown(self, text):
        """
        Translate Atlassian Notation to Markdown

        >>> converter = AtlassianNotationConverter()
        >>> converter.toMarkdown('Blah\\r\\nBlah')
        'Blah  \\nBlah'
        >>> converter.toMarkdown('----')
        '---'
        >>> converter.toMarkdown('h1. Biggest')
        '# Biggest'
        >>> converter.toMarkdown('h2. Bigger')
        '## Bigger'
        >>> converter.toMarkdown('h3. Big')
        '### Big'
        >>> converter.toMarkdown('h4. Normal')
        '#### Normal'
        >>> converter.toMarkdown('h5. Small')
        '##### Small'
        >>> converter.toMarkdown('h6. Smallest')
        '###### Smallest'

        >>> converter.toMarkdown('*strong*')
        '**strong**'
        >>> converter.toMarkdown('_emphasis_')
        '_emphasis_'
        >>> converter.toMarkdown('-deleted-')
        '~~deleted~~'
        >>> converter.toMarkdown('+inserted+')
        '__inserted__'
        >>> converter.toMarkdown('^superscript^')
        '<sup>superscript</sup>'
        >>> converter.toMarkdown('~subscript~')
        '<sub>subscript</sub>'
        >>> converter.toMarkdown('{{monospaced}}')
        '`monospaced`'

        >>> converter.toMarkdown('[http://jira.atlassian.com]')
        'http://jira.atlassian.com'
        >>> converter.toMarkdown('[Atlassian|http://atlassian.com]')
        '[Atlassian](http://atlassian.com)'
        >>> converter.toMarkdown('[mailto:john.doe+jira@domain.tld]')
        '[john.doe+jira@domain.tld](mailto:john.doe+jira@domain.tld)'

        >>> converter.toMarkdown('* unordered list')
        '- unordered list'
        >>> converter.toMarkdown('# ordered list')
        '1. ordered list'

        >>> converter.toMarkdown('||heading 1||heading 2||')
        '|heading 1|heading 2|\\n|---------|---------|'
        """
        tmp = text.strip()
        tmp = re.sub(r'\r\n', r'\n', tmp)
        tmp = re.sub(r'\{(code|noformat).*?\}.*?\{\1\}',
                     self._keepItForLater,
                     tmp, flags=re.DOTALL)
        tmp = re.sub(r'\[.+?\]',
                     self._keepItForLater,
                     tmp, flags=re.MULTILINE)
        tmp = re.sub(r'!.+?!',
                     self._keepItForLater,
                     tmp, flags=re.MULTILINE)
        text = ''
        for line in re.split(r'\n', tmp):
            text += line.strip() + '\n'

        text = re.sub(r'^-{4,}$', r'---\n', text, flags=re.MULTILINE)

        text = re.sub(r'^([\*\#]+) ',
                      self._listsToMarkdown,
                      text, flags=re.MULTILINE)
        text = re.sub(r'^h([1-6])\. (.*)$',
                      self._headingsToMarkdown,
                      text, flags=re.MULTILINE)
        text = re.sub(r'^\|\|.+\|\|$',
                      self._tableHeadingsToMarkdown,
                      text, flags=re.MULTILINE)

        text = re.sub(r':\)', r':smiley:', text)
        text = re.sub(r':\(', r':disappointed:', text)
        text = re.sub(r':P', r':yum:', text)
        text = re.sub(r':D', r':grin:', text)
        text = re.sub(r';\)', r':wink:', text)
        text = re.sub(r'\(y\)', r':thumbsup:', text)
        text = re.sub(r'\(n\)', r':thumbsdown:', text)
        text = re.sub(r'\(i\)', r':information_source:', text)
        text = re.sub(r'\(/\)', r':white_check_mark:', text)
        text = re.sub(r'\(x\)', r':x:', text)
        text = re.sub(r'\(!\)', r':warning:', text)
        text = re.sub(r'\(\+\)', r':heavy_plus_sign:', text)
        text = re.sub(r'\(-\)', r':heavy_minus_sign:', text)
        text = re.sub(r'\(\?\)', r':grey_question:', text)
        text = re.sub(r'\(on\)', r':bulb:', text)
        text = re.sub(r'\(\*[rgby]?\)', r':star:', text)

        text = re.sub(r'~([^\s~].+?[^\s~])~',
                      r'<sub>\1</sub>',
                      text, flags=re.MULTILINE)
        text = re.sub(r'\^([^\s\^].+?[^\s\^])\^',
                      r'<sup>\1</sup>',
                      text, flags=re.MULTILINE)
        text = re.sub(r'\?{2}(.+?)\?{2}',
                      r'\n-- \1\n',
                      text, flags=re.MULTILINE)
        text = re.sub(r'\*([^\s\*].+?[^\s\*])\*',
                      r'**\1**',
                      text, flags=re.MULTILINE)
        text = re.sub(r'(?<!\w)\-([^\s\-].+?[^\s\-])\-(?!\w)',
                      r'~~\1~~',
                      text, flags=re.MULTILINE)
        text = re.sub(r'\+([^\s\+].+?[^\s\+])\+',
                      r'__\1__',
                      text, flags=re.MULTILINE)
        text = re.sub(r'{{(.+?)}}',
                      r'`\1`',
                      text, flags=re.MULTILINE)

        text = re.sub(r'^>\s*bq\. (.*)$', r'\> \1', text, flags=re.MULTILINE)
        text = re.sub(r'\{quote\}[\n\s]*(.*?)[\n\s]*\{quote\}',
                      self._quotesToMarkdown, text, flags=re.DOTALL)
        text = re.sub(r'\{color(?:\:[a-z]+?)?\}[\n\s]*(.*?)[\n\s]*\{color\}',
                      r'\n> **\1**', text, flags=re.DOTALL)

        text = re.sub(r'\n{3,}', r'\n\n', text)
        text = re.sub(r'(?<=\S)\n{1}(?=\w)', r'  \n', text)

        return self._postProcessInMarkdown(text).strip()

    def _keepItForLater(self, match):
        key = '%' + str(len(self._forLater)) + '%'
        self._forLater[key] = match.group(0)
        return key

    def _postProcessInMarkdown(self, text):
        for search, string in self._forLater.items():
            repl = string
            repl = re.sub(r'^\[(.*)\]$', self._linksToMarkdown, repl)
            repl = re.sub(
                r'^!([^|]*)(?:\|.*)?!$',
                self._attachmentsToMarkdown,
                repl)
            r = r'^\{(code|noformat):?(?P<l>[a-z]*?)?\}\n*(?P<c>.+?)\n*\{\1\}$'
            repl = re.sub(
                r,
                r'\n```\g<l>\n\g<c>\n```',
                repl,
                flags=re.DOTALL
            )
            text = re.sub(re.escape(search), repl, text)
        return text


class JiraNotationConverter(AtlassianNotationConverter):
    def __init__(self, issue):
        AtlassianNotationConverter.__init__(self)
        if hasattr(issue.fields, 'attachment'):
            self._attachments = issue.fields.attachment

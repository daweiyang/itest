import unittest

from itest.loader import CaseParser


class CaseParserTest(unittest.TestCase):

    def parse(self, text):
        return CaseParser().parse_string(text)

    def test_continual_line(self):
        case = '''__summary__: hello world
__steps__:
> one command which \\
has two lines
second line that don't start with gt
> third line'''
        p = self.parse(case)

        self.assertEquals('hello world', p.summary)
        self.assertEquals([
            'one command which has two lines',
            'third line'], p.steps)

    def test_comment_ignore(self):
        case = '''#first comment
__summary__: hello case
#second comment
summary here
__steps__:'''
        p = self.parse(case)

        self.assertEquals('hello case\nsummary here',
            p.summary)

    def test_summary_is_required(self):
        with self.assertRaises(SyntaxError):
            self.parse('')

    def test_steps_is_required(self):
        case = '''__summary__: no steps sections'''

        with self.assertRaises(SyntaxError):
            self.parse(case)

    def test_duplicate_section(self):
        case = '''__summary__: a
__summary__: b'''

        with self.assertRaises(SyntaxError):
            self.parse(case)

    def test_output_example_shows_in_steps(self):
        case = '''__summary__: hello world
__steps__:
> cd /tmp
> ls
file.txt dir/
> touch new_file.txt
> ls
file.txt new_file.txt dir/
'''
        p = self.parse(case)

        self.assertEquals([
            'cd /tmp',
            'ls',
            'touch new_file.txt',
            'ls',
            ], p.steps)

    def test_section_header_does_not_contains_comma(self):
        case = '''__summary__
one line summary
__steps__
> cmd1
> cmd2
'''
        p = self.parse(case)

        self.assertEquals('one line summary', p.summary)
        self.assertEquals(['cmd1', 'cmd2'], p.steps)

    def test_invalid_section_header(self):
        case = ''' : section without name'''

        with self.assertRaises(SyntaxError):
            self.parse(case)

    def test_invalid_section_header2(self):
        case = '''__: section without name'''

        with self.assertRaises(SyntaxError):
            self.parse(case)

    def test_qa(self):
        case = '''__summary__: qa
__qa__:
Q: Do you really want to abort(y/N)?
A: certainly

Q: What's this ?
A: !@#$#

__steps__:
> cmd1
'''
        p = self.parse(case)
        self.assertEquals([
            ('Do you really want to abort(y/N)?', 'certainly\n'),
            ("What's this ?", '!@#$#\n'),
            ], p.qa)

    def test_empty_issue(self):
        case = '''__summary__: issue1
__issue__:
__steps__:
> cmd1
'''
        p = self.parse(case)
        self.assertEqual([], p.issue)

    def test_bare_number_issue(self):
        case = '''__summary__: issue1
__issue__: 101
__steps__:
> cmd1
'''
        p = self.parse(case)
        self.assertEqual(['101'], p.issue)

    def test_multi_issues(self):
        case = '''__summary__: issue1
__issue__: 101, 102 103 bug104 #105 feature106
bug-107 , 108 ,109 issue110

__steps__:
> cmd1
'''
        p = self.parse(case)
        self.assertEqual(['101', '102', '103', '104', '105',
                          '106', '107', '108', '109', '110',
                          ],
                         p.issue)

    def test_bad_isssue(self):
        case = '''__summary__: issue1
__issue__: bad guy
__steps__:
> cmd1
'''
        self.assertRaises(SyntaxError, self.parse, case)

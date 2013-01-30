class TestSuite(object):
    '''A set of test cases'''

    def __init__(self):
        self._tests = set()

    def __iter__(self):
        return iter(self._sorted(self._tests))

    @property
    def count(self):
        return sum([ test.count for test in self ])

    def add_test(self, test):
        if hasattr(test, '__iter__'):
            for t in test:
                self.add_test(t)
        else:
            self._tests.add(test)

    def add_tests(self, tests):
        for test in tests:
            self.add_test(test)

    def run(self, result, *args, **kw):
        for test in self:
            if result.should_stop:
                break
            test.run(result, *args, **kw)
        return result

    def _sorted(self, tests):
        #FIXME: should shuffle cases before testing
        # but now GBS build cases can't be shuffled
        #random.shuffle(cases)
        tests2 = list(tests)
        tests2.sort(key=lambda test: test.filename)
        return tests2

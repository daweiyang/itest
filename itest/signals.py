import weakref
import signal


_results = weakref.WeakKeyDictionary()
def register_result(result):
    _results[result] = 1


class _StopHandler(object):

    called = False

    def __init__(self, default_handler):
        self.default_handler = default_handler

    def __call__(self, signum, frame):
        if self.called:
            self.default_handler(signum, frame)

        self.called = True
        for result in _results.keys():
            result.stop('Terminated by signal %d' % signum)


_handler = None
def install_handler():
    global _handler
    if _handler is None:
        default_handler = signal.getsignal(signal.SIGTERM)
        _handler = _StopHandler(default_handler)
        signal.signal(signal.SIGTERM, _handler)

#!/bin/env python
# -*- coding: utf-8 -*-

"""
Base multimechanize transaction
usage:

from webtest import BaseTransaction

class Transaction(BaseTransaction)
    testname = 'pbrtest'

"""

import logging
from .loader import get_test
from .loader import DEFAULT_TESTDIR

log = logging.getLogger(__name__)


class BaseTransaction(object):
    testname = None
    url = None
    timeout = 40

    def __init__(self):
        if not self.testname:
            raise ValueError("testname must be set in Transaction inherited class")
        self.custom_timers = []

    def run(self):
        gctest = self.get_webtest()
        for elapsed, name, doc, error in gctest:
            self.custom_timers[doc] = elapsed
            if error:
                print "ERROR {name} in {elapsed:10.2f}s ({doc}) --> -- ERROR {name}: --\n{error}\n ----".format(**locals())
                #self.driver.save_screenshot('error-{}.png'.format(name))
            else:
                print "Run {name} in {elapsed:10.2f}s ({doc})".format(**locals())
                #self.driver.save_screenshot('ok-{}.png'.format(name))
            assert (not error), error.strip()
        gctest.close()

    def get_webtest(self, timeout=None):
        timeout = timeout or self.timeout
        gctest = get_test(self.testname, url=self.url,
                driver="phantomjs", timeout=timeout)
        if not gctest:
            msg = "WebTest {} not found at dir {}".format(self.testname, DEFAULT_TESTDIR)
            log.error(msg)
            raise IOError(msg)
        return gctest

    def run_single(self):
        """Runs single webtest from multimech Transaction().
        ej:
        if __name__ == '__main__':
            Transatcion().run_single()
        """

        gctest = self.get_webtest()
        gctest.run()

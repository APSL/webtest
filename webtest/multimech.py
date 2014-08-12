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
    timeout = 120

    def __init__(self):
        if not self.testname:
            raise ValueError("testname must be set in Transaction inherited class")
        self.custom_timers = []
        self.gctest = get_test(self.testname, url=self.url,
                driver="phantomjs", timeout=self.timeout)
        if not self.gctest:
            msg = "WebTest {} not found at dir {}".format(self.testname, DEFAULT_TESTDIR)
            log.error(msg)
            raise IOError(msg)

    def run(self):
        for elapsed, name, doc, error in self.gctest:
            self.custom_timers[doc] = elapsed
            print "Exec {name} in {elapsed:10.2f}s ({doc})".format(**locals())
            assert (not error), error

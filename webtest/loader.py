#!/bin/env python
# -*- coding: utf-8 -*-

import inspect
import logging
import sys
import os

DEFAULT_TESTDIR = "/etc/webtests"

log = logging.getLogger(__name__)


def is_webtest(tup):
    """
    Takes (name, object) tuple, returns True if it's a public WebTest subclass.
    https://github.com/locustio/locust/blob/master/locust/main.py#L293
    """
    name, item = tup
    return bool(
        inspect.isclass(item)
        and issubclass(item, WebTest)
        and hasattr(item, "URL")
        and not name == 'WebTest'
        and not name.startswith('_')
    )


def get_test(testfile, testdir=DEFAULT_TESTDIR, *args, **kwargs):
    """WebTest factory"""
    sys.path.insert(0, testdir)
    try:
        imported = __import__(os.path.splitext(testfile)[0])
    except ImportError:
        log.warn("Test {testfile} not found in {testdir}".format(**locals()))
        return None

    webtests = dict(filter(is_webtest, vars(imported).items()))

    try:
        name, Test = webtests.items()[0]
    except IndexError:
        pass
    else:
        log.info("Loading test {}".format(name))
        return Test(*args, **kwargs)


if __name__ == "__main__":
    pass

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: bcabezas@apsl.net


from webtest import __VERSION__
from webtest.base import get_test, DEFAULT_TESTDIR

from optparse import OptionParser
import logging
import sys

DEFAULT_CONFIG_FILE = "/etc/apconf.ini"
NAME = 'webtest'

log = logging.getLogger(NAME)


def main():
    """Opciones test"""
    parser = OptionParser(usage="usage: %prog [options] test_name")
    parser.add_option("--version", "-v", action="store_true")
    parser.add_option("--verbose", "-V", action="store_true")
    parser.add_option("--testdir", "-d", action="store", dest="testdir",
        default=DEFAULT_TESTDIR,
        help="Directory containing tests")

    options, args = parser.parse_args()
    
    level = logging.DEBUG if options.verbose else logging.INFO
    logging.basicConfig(level=level)

    if args:
        test = get_test(args[0], testdir=options.testdir)

        if not test:
            print "Test {} no encontrado en {}".format(args[0], options.testdir)
            return 1

        test.run()
        return 0
    else:
        parser.print_help()
        return 1

    if options.version:
        print "%s v. %s" % (NAME, __VERSION__)
        return 0
    else:
        parser.print_help()
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

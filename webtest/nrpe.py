#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: bcabezas@apsl.net

from webtest import __VERSION__
from webtest.loader import get_test, DEFAULT_TESTDIR

import click
import logging
import sys
import time

NAME = 'webtest'
NAGIOSCODES = {
    'OK': 0,
    'WARNING': 1,
    'CRITICAL': 2,
    'UNKNOWN': 3,
    'DEPENDENT': 4
}

log = logging.getLogger(NAME)

def nagios_return(code, response, times=None):
    """ prints the response message
        and exits the script with one
        of the defined exit codes
        DOES NOT RETURN
    """
    perfdata = None
    out = "{code} : {response}" 
    if times:
        perfdata = " ".join("'{0}'={1:.3}s".format(*t) for t in times.iteritems())
        out += " | {perfdata}"

    print out.format(code=code, response=response, perfdata=perfdata)

    return NAGIOSCODES[code]



def do_test(webtest):
    """runs webtest"""
  
    start = time.time() 
    times = dict()
    for elapsed, name, doc, error in webtest:
        times[doc] = elapsed
        if error:
            total = time.time() - start
            times['total'] = total
            return nagios_return(code='CRITICAL',
                response="Error in {name}: {error}".format(**locals()),
                times=times)
    total = time.time() - start
    times["Total"] = total
    return nagios_return(code='OK',
        response="Test Ok en {}s".format(total), 
        times=times)

@click.command()
@click.option('--testdir', type=click.Path(exists=True, readable=True), 
        default=DEFAULT_TESTDIR,
        help='Directory containing tests')
@click.option('--driver', type=click.Choice(['firefox', 'remote']),
        default='firefox', help='Selenium Driver')
@click.version_option(__VERSION__)
@click.argument('test_name')
def test(testdir, test_name, driver='firefox'):
    """NRPRE nagios Test"""

    webtest = get_test(test_name, testdir=testdir, driver=driver)
    if not webtest:
        return(nagios_return(code='UNKNOWN',
            response="Test {test_name} not found in {testdir}".format(
                **locals())))

    code = do_test(webtest)
    webtest.close()
    sys.exit(code)


if __name__ == '__main__':
    sys.exit(test())

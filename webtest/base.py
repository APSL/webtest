#!/bin/env python
# -*- coding: utf-8 -*-

import time
import functools
import inspect
import logging
import traceback
import sys
from webtest.metrics import get_metrics_client
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.proxy import Proxy, ProxyType
import uuid
from collections import defaultdict
from webtest.screenshots import save_htmls_screenshots
import cgi

log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 5
LIMIT_EXCEPTION_CHARS = 300
SCREENSHOTS_URL_PREFIX = "https://s3-eu-west-1.amazonaws.com/wachiman-speed"

def step(func=None, order=1):
    """Decorador para step. para obtener tiempo"""

    if func is None:
        return functools.partial(step, order=order)

    def format_traceback(trace):
        result = ""
        for index, s_trace in enumerate(trace.split("File")):
            if index > 0:
                result += "File "
            result += s_trace[:LIMIT_EXCEPTION_CHARS]
        return result

    def format_exception(e, step_name, step_doc):
        exc_info = sys.exc_info()
        trace = format_traceback("".join(traceback.format_exception(*exc_info)))
        msg = str(e)[:LIMIT_EXCEPTION_CHARS]
        error = u"{type_error} error in step {step_name} ({step_doc}).\n{trace}\n-----------\n{msg}".format(
                    type_error=type(e), step_name=step_name, step_doc=step_doc, trace=trace, msg=msg)
        
        return error

    @functools.wraps(func)
    def f(*args, **kwargs):
        error = None
        step_name = func.__name__
        step_doc = func.__doc__
        t1 = time.time()
        try:
            func(*args, **kwargs)
        except Exception as e:
            error = format_exception(e, step_name, step_doc)
        elapsed = time.time() - t1
        return elapsed, step_name, step_doc, error
    f.order = order
    return f


class WebTest(object):
    """Clase base para tests"""
    URL = ''

    DRIVER_FIREFOX = 'firefox'
    DRIVER_PHANTOMJS = 'phantomjs'
    DRIVER_REMOTE = 'remote'
    DRIVER_CHOICES = (
        (DRIVER_FIREFOX, webdriver.Firefox),
        (DRIVER_PHANTOMJS, webdriver.PhantomJS),
        (DRIVER_REMOTE, webdriver.Remote),
    )
    DRIVER_ARGS = {
        DRIVER_PHANTOMJS:  {
            "service_args": ['--ignore-ssl-errors=true', ]
        },
        DRIVER_FIREFOX: {
        },
        DRIVER_REMOTE: {
            'command_executor': 'http://hub:4444/wd/hub',
            'desired_capabilities': DesiredCapabilities.FIREFOX,
            },
    }

    def __init__(self, driver=DRIVER_PHANTOMJS, url=None,
            timeout=DEFAULT_TIMEOUT, proxy=None, stats=False,
            stats_name='webtest'):
        # proxy = "url_sin_http:port"
        kwargs = self.DRIVER_ARGS[driver]
        if proxy:
            selenium_proxy = Proxy(
                {'proxyType': ProxyType.MANUAL,
                'httpProxy': proxy,
                'sslProxy': proxy,
                })
            kwargs["proxy"] = selenium_proxy
        try:
            self.driver = dict(self.DRIVER_CHOICES)[driver](**kwargs)
        except KeyError:
            self.driver = webdriver.PhantomJS()
        self.timeout = timeout
        self.driver.implicitly_wait(timeout)
        self.wait = WebDriverWait(self.driver, timeout)
        self.url = url or self.URL
        self.stats = stats
        self.stats_name = stats_name

    def close(self):
        self.driver.quit()

    def wait_for_id(self, name, timeout=None):
        """calls selenium webdriver wait for ID name"""
        if not timeout:
            timeout = self.timeout
        WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.ID, name)))

    def wait_for_class(self, name):
        """calls selenium webdriver wait for class name"""
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, name)))

    def wait_for_xpath(self, name):
        """calls selenium webdriver wait for xpath"""
        self.wait.until(EC.visibility_of_element_located((By.XPATH, name)))

    def wait_for_css_selector(self, name):
        """calls selenium webdriver wait for css"""
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, name)))

    def wait_for_css_selector_in_element(self, web_element, name):
        """calls selenium webdriver wait for css, search in web_element"""
        WebDriverWait(web_element, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, name)))

    def __iter__(self):
        steps = inspect.getmembers(self, predicate=inspect.ismethod)
        steps = [s for _, s in steps if hasattr(s, "order")]
        steps.sort(key=lambda f: f.order)
        for s in steps:
            yield s()

    def run(self):
        ok_stats = defaultdict(list)
        err_stats = defaultdict(list)
        if self.stats:
            client = get_metrics_client()

        test_uid = str(uuid.uuid1())
        init_test_time = time.time()

        for elapsed, name, doc, error in self:
            if error:

                error_html="""
<div style="height:700px">
    <table>
        <tr>
            <td>
                <img width="300px" valign="top" src='{img_src}' />
            </td>
            <td width="300px" style="font-size:8px">
                <font size="1">
                    {error}
                </font>
            </td>
    </table>
</div>
"""
                print u"ERROR {name} in {elapsed:10.2f}s ({doc}) --> [[{error}]]".format(**locals())
                error = cgi.escape(error)
                img_src = "{}/{}/errors/{}/{}_{}.png".format(
                    SCREENSHOTS_URL_PREFIX, self.stats_name, name, name, test_uid)
                err_stats["{}.{}.errors".format(self.stats_name, name)].append(
                    [time.time(),
                    error_html.format(error=error, img_src=img_src),
                    test_uid])
                break
            else:
                print u"Run {name} in {elapsed:10.2f}s ({doc})".format(**locals())
                ok_stats["{}.{}".format(self.stats_name, name)].append([time.time(), elapsed, test_uid])

        elapsed_test_time = time.time() - init_test_time
        print u"Total in {}".format(elapsed_test_time)

        if self.stats:
            points = [{
                'points': [[time.time(), test_uid]],
                'name': '{}.executions'.format(self.stats_name),
                'columns': ['time', "test_uid"]
            }]
            if not err_stats: # Tiempo Total
                points.append({
                    'points': [[time.time(), elapsed_test_time, test_uid]],
                    'name': '{}.total'.format(self.stats_name),
                    'columns': ['time', "elapsed", "test_uid"]
                })
                save_htmls_screenshots("{}/oks".format(self.stats_name), self.driver, "{}_{}".format(name, test_uid), push_to_s3=True)
            else:
                save_htmls_screenshots("{}/errors/{}".format(self.stats_name, name), self.driver, "{}_{}".format(name, test_uid), push_to_s3=True)
            for key, value in err_stats.iteritems():
                points.append({
                            'points': value,
                            'name': key,
                            'columns': ['time', "error", "test_uid"]
                        })
            for key, value in ok_stats.iteritems():
                points.append({
                        'points': value,
                        'name': key,
                        'columns': ['time', 'elapsed', "test_uid"]
                    })
            client.write_points(points)
        self.close()


if __name__ == "__main__":
    pass

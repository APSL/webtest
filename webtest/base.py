#!/bin/env python
# -*- coding: utf-8 -*-

import time
import functools
import inspect
import logging
import traceback
import sys
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 5


def step(func=None, order=1):
    """Decorador para step. para obtener tiempo"""

    if func is None:
        return functools.partial(step, order=order)

    @functools.wraps(func)
    def f(*args, **kwargs):
        error = None
        step_name = func.__name__
        step_doc = func.__doc__
        t1 = time.time()
        try:
            func(*args, **kwargs)
        except TimeoutException, e:
            error = u"Timeout step {step_name} ({step_doc}). {e}".format(**locals())
        except Exception as e:
            exc_info = sys.exc_info()
            trace = "".join(traceback.format_exception(*exc_info))
            error = u"Error step {step_name} ({step_doc}). {msg}.\n{trace}".format(
                    step_name=step_name, step_doc=step_doc,
                    msg=e.msg, trace=trace)

        elapsed = time.time() - t1
        return elapsed, step_name, step_doc, error
    f.order = order
    return f


class WebTest(object):
    """Clase base para tests"""
    URL = ''

    DRIVER_FIREFOX = 'firefox'
    DRIVER_PHANTOMJS = 'phantomjs'
    DRIVER_CHOICES = (
        (DRIVER_FIREFOX, webdriver.Firefox),
        (DRIVER_PHANTOMJS, webdriver.PhantomJS)
    )
    DRIVER_ARGS = {
        DRIVER_PHANTOMJS:  {
            "service_args": [ '--ignore-ssl-errors=true', ]
        },
        DRIVER_FIREFOX: {}
    }

    def __init__(self, driver=DRIVER_PHANTOMJS, url=None,
            timeout=DEFAULT_TIMEOUT, proxy=None, trace=False):
        from selenium.webdriver.common.proxy import Proxy, ProxyType

        #proxy_url = "http://localhost:8088"
        # proxy = Proxy()
        # proxy.http_proxy = proxy_url
        #{
            #'proxyType': ProxyType.MANUAL,
            #'httpProxy': proxy_url})
        #service_args = [
            #'--proxy=127.0.0.1:8088',
            #'--proxy-type=http',
        #]

        kwargs = self.DRIVER_ARGS[driver]
        try:
            self.driver = dict(self.DRIVER_CHOICES)[driver](**kwargs)
        except KeyError:
            self.driver = webdriver.PhantomJS()
        self.driver.implicitly_wait(timeout)
        self.wait = WebDriverWait(self.driver, timeout)
        self.url = url or self.URL
        self.trace = trace

    def wait_for_id(self, name):
        """calls selenium webdriver wait for ID name"""
        self.wait.until(EC.presence_of_element_located((By.ID, name)))

    def wait_for_class(self, name):
        """calls selenium webdriver wait for class name"""
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, name)))

    def wait_for_xpath(self, name):
        """calls selenium webdriver wait for xpath"""
        self.wait.until(EC.presence_of_element_located((By.XPATH, name)))

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
        for elapsed, name, doc, error in self:
            if error:
                print u"ERROR {name} in {elapsed:10.2f}s ({doc}) --> [[{error}]]".format(**locals())
                #self.driver.save_screenshot('error-{}.png'.format(name))
                sys.exit(1)
            else:
                print u"Run {name} in {elapsed:10.2f}s ({doc})".format(**locals())
                #self.driver.save_screenshot('ok-{}.png'.format(name))
        self.close()

    def close(self):
        self.driver.close()


if __name__ == "__main__":
    pass

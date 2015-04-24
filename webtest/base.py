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
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.proxy import Proxy, ProxyType
from statistics import StatisticsClient
import uuid

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
                    msg=e, trace=trace)

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
            "service_args": [ '--ignore-ssl-errors=true', ]
        },
        DRIVER_FIREFOX: {
        },
        DRIVER_REMOTE: {
            'command_executor': 'http://127.0.0.1:4444/wd/hub',
            'desired_capabilities': DesiredCapabilities.FIREFOX,
            },
    }

    def __init__(self, driver=DRIVER_PHANTOMJS, url=None,
            timeout=DEFAULT_TIMEOUT, proxy=None, stats=False, stats_name='webtest'):        
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
        ok_stats = []
        err_stat = None

        test_uid = str(uuid.uuid1())
        init_test_time = time.time()
        for elapsed, name, doc, error in self:
            if error:
                print u"ERROR {name} in {elapsed:10.2f}s ({doc}) --> [[{error}]]".format(**locals())
                #self.driver.save_screenshot('error-{}.png'.format(name))
                err_stat = [time.time(), name, error, test_uid]
                break
            else:
                print u"Run {name} in {elapsed:10.2f}s ({doc})".format(**locals())
                #self.driver.save_screenshot('ok-{}.png'.format(name))
                ok_stats.append([time.time(), name, elapsed, test_uid])
        elapsed_test_time = time.time() - init_test_time
        print u"Total in {}".format(elapsed_test_time)

        if self.stats:
            stats_client = StatisticsClient()
            points =    [{
                            'points': [[time.time(), "total", elapsed_test_time, test_uid]],
                            'name': self.stats_name,
                            'columns': ['time', "step", "elapsed", "test_uid"]
                        }]
            if err_stat:
                points.append({
                            'points': [err_stat],
                            'name': '{}_errors'.format(self.stats_name),
                            'columns': ['time', "step", "error", "test_uid"]
                        })
            if ok_stats:
                points.append({
                        'points': ok_stats,
                        'name': self.stats_name,
                        'columns': ['time', 'step', 'elapsed', "test_uid"]
                    })
            stats_client.write_points(points)

        self.close()



if __name__ == "__main__":
    pass

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


def format_traceback(trace):
    result = ""
    for index, s_trace in enumerate(trace.split("File")):
        if index > 0:
            result += "- File "
        result += s_trace[:LIMIT_EXCEPTION_CHARS]
    return result


def format_exception(e, step_name, step_doc):
    exc_info = sys.exc_info()
    trace = format_traceback("".join(traceback.format_exception(*exc_info)))
    msg = str(e)[:LIMIT_EXCEPTION_CHARS]
    error = u"{type_error} error in step {step_name} ({step_doc}).\n{trace}\n-----------\n{msg}".format(
                type_error=type(e), step_name=step_name, step_doc=step_doc, trace=trace, msg=msg)
    return error


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
        except Exception as e:
            error = format_exception(e, step_name, step_doc)
        elapsed = time.time() - t1
        return elapsed, step_name, step_doc, error
    f.order = order
    return f

class AnyCondition(object):
    """ Clase para usar con WebDriverWait """
    def __init__(self, *args):
        self.conditions = args

    def __call__(self, driver):
        for cond in self.conditions:
            try:
                return cond(driver)
            except:
                pass
        return False

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
            stats_name='webtest', serie_sufix=None,
            min_window_width=None, influx_conf=None, screenshots_conf=None):
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

        self._set_min_width(min_window_width)
        self.timeout = timeout
        self.driver.implicitly_wait(timeout)
        self.wait = WebDriverWait(self.driver, timeout)
        self.url = url or self.URL
        self.stats = stats
        self.stats_name = stats_name
        self.serie_sufix = serie_sufix
        self.influx_conf = influx_conf
        self.screenshots_conf = screenshots_conf

    def _set_min_width(self, min_width):
        """Sets minimal width"""
        if min_width:
            size = self.driver.get_window_size()
            width = size.get('width')
            height = size.get('height')
            if width < min_width:
                self.driver.set_window_size(min_width, height)

    def close(self):
        self.driver.quit()

    def wait_for_id(self, name, timeout=None, visible=False):
        """calls selenium webdriver wait for ID name"""
        self.driver.implicitly_wait(0.5)
        if not timeout:
            timeout = self.timeout
        if visible:
            found_element = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.ID, name)))
        else:
            found_element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.ID, name)))
        self.driver.implicitly_wait(self.timeout) # Restauramos implicitly_wait
        return found_element

    def wait_for_class(self, name):
        """calls selenium webdriver wait for class name"""
        self.driver.implicitly_wait(0.5)
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, name)))
        self.driver.implicitly_wait(self.timeout) # Restauramos implicitly_wait


    def wait_for_xpath(self, name, timeout=None, visible=False):
        """calls selenium webdriver wait for xpath"""
        self.driver.implicitly_wait(0.5)
        if not timeout:
            timeout = self.timeout
        if visible:
            found_element = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.XPATH, name)))
        else:
            found_element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, name)))
        self.driver.implicitly_wait(self.timeout) # Restauramos implicitly_wait
        return found_element

    def wait_for_css_selector(self, name, timeout=None, visible=False):
        """calls selenium webdriver wait for css"""
        self.driver.implicitly_wait(0.5)
        if not timeout:
            timeout = self.timeout
        if visible:
            found_element = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, name)))
        else:
            found_element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, name)))
        self.driver.implicitly_wait(self.timeout) # Restauramos implicitly_wait
        return found_element

    def wait_for_css_selector_in_element(self, web_element, name):
        """calls selenium webdriver wait for css, search in web_element"""
        self.driver.implicitly_wait(0.5)
        found_element = WebDriverWait(web_element, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, name)))
        self.driver.implicitly_wait(self.timeout) # Restauramos implicitly_wait
        return found_element

    def wait_until(self, condition, timeout=None):
        self.driver.implicitly_wait(0.1)
        if not timeout:
            timeout = self.timeout
        found_element =  WebDriverWait(self.driver, timeout).until(condition)
        self.driver.implicitly_wait(self.timeout) # Restauramos implicitly_wait
        return found_element

    def _get_steps(self):
        steps = inspect.getmembers(self, predicate=inspect.ismethod)
        steps = [s for _, s in steps if hasattr(s, "order")]
        steps.sort(key=lambda f: f.order)
        return steps

    def __iter__(self):
        for step in self._get_steps():
            yield step()

    def _compose_serie_name(self, name, error, serie_sufix):
        """ Wrapper para componer el nombre de las series """
        serie_name = name
        if error:
            serie_name += ".errors"
        if serie_sufix:
            serie_name += ".{}".format(serie_sufix)
        return serie_name

    def run(self):
        ok_stats = defaultdict(list)
        err_stats = defaultdict(list)

        test_uid = str(uuid.uuid1())
        init_test_time = time.time()

        for elapsed, name, doc, error in self:
            if error:

# <style>
    #webtest_error pre {{ vertical-align:top !important; font-size:10px !important; font-weight:normal !important; }}
    #webtest_error td {{ vertical-align:top !important; }}
    #webtest_error {{ max-height:575px !important; }}
# </style>

                error_html="""
<div id="webtest_error">
    <table>
        <tbody>
        <tr>
            <td width="300">
                <img width="300px" src='{img_src}'/>
            </td>
            <td width="500">
                <font size="1">
                    {error}
                </font>
            </td>
        </tr>
        </tbody>
    </table>
</div>
"""
                print u"ERROR {name} in {elapsed:10.2f}s ({doc}) --> [[{error}]]".format(**locals())
                error = cgi.escape(error)
                error = error.replace("\n", "<br>")
                img_src = "{}/{}/errors/{}/{}_{}.png".format(
                    self.screenshots_conf["SCREENSHOTS_URL_PREFIX"], self.stats_name, name, name, test_uid)
                
                serie_name = self._compose_serie_name("{}.{}".format(self.stats_name, name), error, self.serie_sufix)

                # serie_name = "{}.{}.errors".format(self.stats_name, name)
                # if self.serie_sufix:
                #     serie_name += ("." + self.serie_sufix)
                err_stats[serie_name].append(
                    [time.time(),
                    elapsed,
                    error_html.format(error=error, img_src=img_src),
                    test_uid])
                break
            else:
                print u"Run {name} in {elapsed:10.2f}s ({doc})".format(**locals())

                serie_name = self._compose_serie_name("{}.{}".format(self.stats_name, name), error, self.serie_sufix)

                # serie_name = "{}.{}".format(self.stats_name, name)
                # if self.serie_sufix:
                #     serie_name += ("." + self.serie_sufix)
                ok_stats[serie_name].append([time.time(), elapsed, test_uid])

        elapsed_test_time = time.time() - init_test_time
        print u"Total in {}".format(elapsed_test_time)

        if self.stats:
            serie_name  = self._compose_serie_name('{}.executions'.format(self.stats_name), False, self.serie_sufix)
            points = [{
                'points': [[time.time(), test_uid]],
                'name': serie_name,
                'columns': ['time', "test_uid"]
            }]
            if not err_stats:
                # Tiempo Total
                serie_name  = self._compose_serie_name('{}.total'.format(self.stats_name), False, self.serie_sufix)
                points.append({
                    'points': [[time.time(), elapsed_test_time, test_uid]],
                    'name': serie_name,
                    'columns': ['time', "elapsed", "test_uid"]
                })
                
            for key, value in err_stats.iteritems():
                points.append({
                            'points': value,
                            'name': key,
                            'columns': ['time', 'elapsed', "error", "test_uid"]
                        })
            for key, value in ok_stats.iteritems():
                points.append({
                        'points': value,
                        'name': key,
                        'columns': ['time', 'elapsed', "test_uid"]
                    })
            

            client = get_metrics_client(self.influx_conf)
            client.write_points(points)

            try:
                if self.screenshots_conf:
                    if not err_stats:
                        save_htmls_screenshots("{}/oks".format(self.stats_name), self.driver,
                            "{}_{}".format(name, test_uid), self.screenshots_conf)
                    else:
                        save_htmls_screenshots("{}/errors/{}".format(self.stats_name, name),
                            self.driver, "{}_{}".format(name, test_uid), self.screenshots_conf)
            except:
                exc_info = sys.exc_info()
                trace = "".join(traceback.format_exception(*exc_info))
                log.error(trace)

        self.close()


if __name__ == "__main__":
    pass

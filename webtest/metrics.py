#!/bin/env python
# -*- coding: utf-8 -*-

"""
Metrics backend for webtest
"""

from influxdb.influxdb08 import InfluxDBClient
import os


def get_metrics_client():
    host = os.getenv('INFLUXDB_HOST', 'localhost')
    port = os.getenv('INFLUXDB_PORT', 8086)
    user = os.getenv('INFLUXDB_USER', 'root')
    passwd = os.getenv('INFLUXDB_PASS', 'root')
    dbname = os.getenv('INFLUXDB_DBNAME', 'mydata')

    client = InfluxDBClient(host, port, user, passwd, dbname)
    return client

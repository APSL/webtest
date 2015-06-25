#!/bin/env python
# -*- coding: utf-8 -*-

"""
Metrics backend for webtest
"""

from influxdb.influxdb08 import InfluxDBClient

def get_metrics_client(influx_conf):
    if not influx_conf:
        raise Exception("Se ha intentado conectar a Influx sin los datos de conexion")

    client = InfluxDBClient(influx_conf["HOST"], influx_conf["PORT"], influx_conf["USER"], influx_conf["PASSWD"], influx_conf["DBNAME"])
    return client

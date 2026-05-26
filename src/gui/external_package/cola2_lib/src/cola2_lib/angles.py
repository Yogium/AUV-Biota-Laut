#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2019 Iqua Robotics SL - All Rights Reserved
#
# This file is subject to the terms and conditions defined in file
# 'LICENSE.txt', which is part of this source code package.

import math
from math import pi, floor
import numpy as np

def wrap_angle(angle):
    """ Wraps angle between 0 and 2 pi """
    return (angle + ( 2.0 * pi * floor( ( pi - angle ) / ( 2.0 * pi ) ) ) )

""" Angle unit conversions """

def degree_minutes_to_degrees(lat, lon):
    """ Transforms latitude and longitude in the format
        DDDMM.MM to the format DDD.DD """
    lat_deg, lat_min = __split_degree_minutes__(lat)
    lon_deg, lon_min = __split_degree_minutes__(lon)
    return lat_deg + lat_min/60.0, lon_deg + lon_min/60.0

def degrees_to_degree_minutes(lat, lon):
    """ Transforms latitude and longitude in the format
        DDD.DD to the format DDDMM.MM """
    lat_degree = __degree_to_degree_minutes_aux__(lat)
    lon_degree = __degree_to_degree_minutes_aux__(lon)
    return lat_degree, lon_degree

def degrees_to_degree_minute_seconds(lat, lon):
    '''
    Transforms coordinates from DDD.DDDDD (float) to a string of
    DDDºMM'SS.SSS''
    @param lat: latitude
    @type lat: float
    @param lon: longitude
    @type lon: float
    '''
    lat_str = __degree_to_degree_minute_seconds_aux__(lat)
    lon_str = __degree_to_degree_minute_seconds_aux__(lon)
    return [lat_str, lon_str]


def __degree_to_degree_minute_seconds_aux__(value):
    '''
    Transforms coordinates from DDD.DDDDD (float) to a string of
    DDDºMM'SS.SSS''
    @param value: value in DDD.DDDDD
    @type value: float
    '''
    d = int(value)
    t = (value - d) * 60
    m = int(t)
    s = (t - m) * 60
    return "{:03d}º {:02d}' {:06.3f}''".format(d, m, s)


def __degree_to_degree_minutes_aux__(value):
    val = str(value).split('.')
    minute = float('0.' + val[1]) * 60.0
    if minute < 10.0:
        return float(val[0] + '0' + str(minute))
    else:
        return float(val[0] + str(minute))

def __split_degree_minutes__(value):
    """ Transform DDDMM.MM to DDD, MM.MM """
    val = str(value).split('.')
    val_min = val[0][-2] + val[0][-1] + '.' + val[1]
    val_deg = ''
    for i in range(len(val[0])-2):
        val_deg = val_deg + val[0][i]

    return int(val_deg), float(val_min)

def test() :

    print "Normalize angle 7.14 = " + str(wrap_angle(7.14))
    result=degree_minutes_to_degrees('04156.74','00002.48')
    print "degree_mintues_to_degrees 4156.74, 0002.48 (DDMM.MM) = " + str(result)
    print "degrees_to_degree_minutes "+ str(result) + " (DDDD.DD) = " + str(degrees_to_degree_minute_seconds(result[0],result[1]))
    result2=degrees_to_degree_minute_seconds(result[0],result[1])
    print "degrees_to_degree_minute_seconds " + str(result) + " (DDDD.DD) = " + str(result2[0]) + str(result2[1])


if __name__ == '__main__':
    test()

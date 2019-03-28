#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 22 11:28:24 2019

@author: jan kunkler
"""

"""
Math Inspired by:
KittyL (https://math.stackexchange.com/users/206286/kittyl), 
Working out coordinates for a bounding box with 3 mile radius from original lat/long, 
URL (version: 2015-02-13): https://math.stackexchange.com/q/1146457
"""

import math

def boundingBox(lat, lon, s=0.15, mode=2):
    """
    Arguments:
        lat: Latitude of location
        lon: Longitude of location
        s: arc length in km, default 0.15km radius around center point
        mode: Select which boundaries to return
    """
    
    """
    Modes:
        1: return all four boundaries upper left, upper right, lower left, lower right
        2: return only upper left and lower right boundaries
    """
    
    r = 3963 # radius of earth in miles
    
    # convert coordinates to Radians
    lat_rad = lat * math.pi / 180
    lon_rad = lon * math.pi / 180
    
    upper_right = (lat_rad + s/r, lon_rad + s/r)
    lower_right = (lat_rad + s/r, lon_rad - s/r)
    upper_left = (lat_rad - s/r, lon_rad + s/r)
    lower_left = (lat_rad - s/r, lon_rad - s/r)
    
    coordinates = (upper_left, upper_right, lower_left, lower_right)
    
    bounds = []
    # convert Radians back to Degrees
    for c in coordinates:
        bounds.append(tuple(x*180/math.pi for x in c))
    
    if mode == 1:
        return bounds
    elif mode == 2:
        return bounds[0], bounds[3]
    else:
        return bounds

    
def main():
    upper_left, lower_right = boundingBox(48.994435, 12.111247)
    print(upper_left, lower_right)
 
    
if __name__ == '__main__':  main()
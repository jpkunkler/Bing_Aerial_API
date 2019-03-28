# -*- coding: utf-8 -*-
"""
author: jan kunkler (jpkunkler)
date: March 25, 2019
reference: https://docs.microsoft.com/en-us/bingmaps/articles/bing-maps-tile-system
"""

import math
from itertools import chain
import re

class TileSystem(object):
    
    EARTHRADIUS = 6378137
    MINLAT, MAXLAT  = -85.05112878, 85.05112878
    MINLON, MAXLON= -180, 180
    TILESIZE = 256 # BING Maps use 256x256 tiles
    
    @staticmethod
    def clip(n, minValue, maxValue):
        """
        Clips a number to the specified minimum and maximum value.
        
        Args:
            n (double):         The number to clip.
            minvalue (double):  Minimum allowable value.
            maxvalue (double):  Maximum allowable value.
        Returns:
            double: The clipped value.
        """
        
        return min(max(n, minValue), maxValue)
    
    @staticmethod
    def mapSize(levelOfDetail):
        """
        Determines the map width and height (in pixels) at a specific level.
        
        Args:
            levelOfDetail (int): Level of detail, from 1 (lowest detail) to 23 (highest detail).
        Returns:
            int: The map width and height in pixels.
        
        """
        
        return 256 << levelOfDetail
    
    @staticmethod
    def groundResolution(latitude, levelOfDetail):
        """
        Determines the ground resolution (in meters per pixel) at a specified  
        latitude and level of detail.
        
        Args:
            latitude (double):      Latitude (in degrees) at which to measure the  ground resolution.
            levelOfDetail (int):    Level of detail, from 1 (lowest detail) to 23 (highest detail).    
        Returns:
            double: The ground resolution, in meters per pixel.
        
        """
        
        latitude = TileSystem.clip(latitude, self.MINLAT, TileSystem.MAXLAT)
        return math.cos(latitude * math.pi / 180) * 2 * math.pi * TileSystem.EARTHRADIUS / TileSystem.mapSize(levelOfDetail)
        

    @staticmethod
    def mapScale(latitude, levelOfDetail, screenDpi):
        """
        Determines the map scale at a specified latitude, level of detail,  
        and screen resolution. 
        
        Args:
            latitude (double):      Latitude (in degrees) at which to measure the  ground resolution.
            levelOfDetail (int):    Level of detail, from 1 (lowest detail) to 23 (highest detail).    
            screemDpi (int):        Resolution of the screen, in dots per inch.
        Returns:
            double: The map scale, expressed as the denominator N of the ratio 1 : N.
        
        """
        
        return TileSystem.groundResolution(latitude, levelOfDetail) * screenDpi / 0.0254
    
    @staticmethod
    def latLongToPixelXY(latitude, longitude, levelOfDetail):
        """
        Converts a point from latitude/longitude WGS-84 coordinates (in degrees)  
        into pixel XY coordinates at a specified level of detail.
        
        Args:
            latitude (double):      Latitude of the point, in degrees.
            longitude (double):     Longitude of the point, in degrees.
            levelOfDetail (int):    Level of detail, from 1 (lowest detail) to 23 (highest detail).
            
        Returns:
            pixelX (int):   X coordinate in pixels.
            pixelY (int):   Y coordinate in pixels.
        """
        latitude = TileSystem.clip(latitude, TileSystem.MINLAT, TileSystem.MAXLAT)
        longitude = TileSystem.clip(longitude, TileSystem.MINLON, TileSystem.MAXLON)
        
        x = (longitude + 180) / 360
        sinLatitude = math.sin(latitude * math.pi / 180)
        y = 0.5 - math.log((1 + sinLatitude) / (1 - sinLatitude)) / (4 * math.pi)
        
        mapSize = TileSystem.mapSize(levelOfDetail)
        pixelX = int(TileSystem.clip(x * mapSize + 0.5, 0, mapSize - 1))
        pixelY = int(TileSystem.clip(y * mapSize + 0.5, 0, mapSize - 1))
        
        return pixelX, pixelY
    
    @staticmethod
    def pixelXYToLatLong(pixelX, pixelY, levelOfDetail):
        """
        Converts a pixel from pixel XY coordinates at a specified level of detail  
        into latitude/longitude WGS-84 coordinates (in degrees).
        
        Args:
            pixelX (int):       X coordinate of the point, in pixels.
            pixelY (int):       Y coordinate of the point, in pixels.
            levelOfDetail(int): Level of detail, from 1 (lowest detail) to 23 (highest detail).
            
        Returns:
            latitude (double):      Latitude in degrees.
            longitude (double):     Longitude in degrees.
    
        """
        
        mapSize = TileSystem.mapSize(levelOfDetail)
        x = (TileSystem.clip(pixelX, 0, mapSize - 1) / mapSize) - 0.5
        y = 0.5 - (TileSystem.clip(pixelY, 0, mapSize - 1) / mapSize)
        
        latitude = 90 - 360 * math.atan(math.exp(-y * 2 * math.pi)) / math.pi
        longitude = 360 * x
        
        return latitude, longitude
    
    @staticmethod
    def pixelXYToTileXY(pixelX, pixelY):
        """
        Converts pixel XY coordinates into tile XY coordinates of the tile containing  
        the specified pixel.
        
        Args:
            pixelX (int):   Pixel X Coordinate.
            pixelY (int):   Pixel Y Coordinate.
            
        Returns:
            tileX (int):    Map Tile X coordinate.
            tileY (int):    Map Tile Y coordinate.
            
        """
        
        tileX = pixelX / TileSystem.TILESIZE
        tileY = pixelY / TileSystem.TILESIZE
        
        return int(tileX), int(tileY)
    
    @staticmethod
    def tileXYToPixelXY(tileX, tileY):
        """
        Converts pixel XY coordinates into tile XY coordinates of the tile containing  
        the specified pixel.
        
        Args:
            tileX (int):   Tile X Coordinate.
            tileY (int):   Tile Y Coordinate.
            
        Returns:
            pixelX (int):    Map Tile X coordinate.
            pixelY (int):    Map Tile Y coordinate.
            
        """
        
        pixelX = tileX * TileSystem.TILESIZE
        pixelY = tileY * TileSystem.TILESIZE
        
        return int(pixelX), int(pixelY)
    
    
    @staticmethod
    def tileXYToQuadKey(tileX, tileY, levelOfDetail):
        """
        Converts tile XY coordinates into a QuadKey at a specified level of detail.
        
        Args:
            tileX (int):            Tile X Coordinate.
            tileY (int):            Tile Y Coordinate.
            levelOfDetail (int):    Level of detail, from 1 (lowest detail) to 23 (highest detail).
            
        Returns:
            str:    A string containing the Quadrant Key.
        """
        
        # Thanks to Linlin Chen for this great workaround!
        
        tileXbits = '{0:0{1}b}'.format(tileX, levelOfDetail)
        tileYbits = '{0:0{1}b}'.format(tileY, levelOfDetail)
        
        quadkeybinary = ''.join(chain(*zip(tileYbits, tileXbits)))
        return ''.join([str(int(num, 2)) for num in re.findall('..?', quadkeybinary)])
            
    
    @staticmethod
    def quadKeyToTileXY(quadKey):
        """
        Converts a QuadKey into tile XY coordinates.  
        
        Args:
            quadKey (str):  QuadKey of the tile.
        
        Returns:
            tileX (int):            Tile X Coordinate.
            tileY (int):            Tile Y Coordinate.
            levelOfDetail (int):    Level of Detail.
        """
        
        # Thanks to Linlin Chen for this great workaround!
        
        quadkeybinary = ''.join(['{0:02b}'.format(int(num)) for num in quadKey])
        tileX, tileY = int(quadkeybinary[1::2], 2), int(quadkeybinary[::2], 2)
        return tileX, tileY
        
        
        
        
        
        
        
# -*- coding: utf-8 -*-
"""
Author: Jan Pascal Kunkler
Date: 25.03.2019
Credit to Linlin Chen (https://github.com/llgeek/Satellite-Aerial-Image-Retrieval) for providing the base code.
Modified and Updated to use the latest Bing Maps API standards (2019).
"""

MAXSIZE = 8192 * 8192 * 8 # maximum image size possible

import datetime
from PIL import Image
import requests
from urllib import request
import os, sys

# import our bing tile system handler class
from bingTileSystem import TileSystem as ts
from BoundingBox import boundingBox as bb

# https://docs.microsoft.com/en-us/bingmaps/rest-services/imagery/get-imagery-metadata
BING_AVAILABILITY_URL = "http://dev.virtualearth.net/REST/V1/Imagery/Metadata/Aerial?output=json&key="

class BingAerialImage(object):
    
    def __init__(self, lat, lon, s=0.15):
        self.lat = lat
        self.lon = lon
        self.arc = s
        self.upper_left = bb(self.lat, self.lon, self.arc, 2)[0] # tupel (X,Y)
        self.lower_right = bb(self.lat, self.lon, self.arc, 2)[1] # tupel (X,Y)
        self.api_key = open("apikey.txt", "r").readline().rstrip()
        
        self.currentBaseURL() # retrieve currently available domains for aerial images
          
        self.tgtfolder = './output/'
        try:
            os.makedirs(self.tgtfolder)
        except FileExistsError:
            pass
        except OSError:
            raise
            
    def currentBaseURL(self):
        """
        Retrieve the currently available URL for Bing's Aerial Imagery REST API by pinging the official interface.
        This guarantees that the most up-to-date API will always be used.
        """
        r = requests.get(BING_AVAILABILITY_URL + self.api_key)
        if r.status_code != 200:
            raise Exception("API Call to Bing Maps failed.")
            sys.exit()
        
        self.baseURL = r.json()["resourceSets"][0]["resources"][0]["imageUrl"]
        self.subdomains = r.json()["resourceSets"][0]["resources"][0]["imageUrlSubdomains"]
        self.tileSize = r.json()["resourceSets"][0]["resources"][0]["imageHeight"]
        self.maxZoom = r.json()["resourceSets"][0]["resources"][0]["zoomMax"]
    
    
    def download_image(self, quadkey):
        """This method is used to download a tile image given the quadkey from Bing tile system
        
        Arguments:
            quadkey {[string]} -- [The quadkey for a tile image]
        
        Returns:
            [Image] -- [A PIL Image]
        """

        with request.urlopen(self.baseURL.format(subdomain=self.subdomains[0],quadkey=quadkey)) as file:
            return Image.open(file)
 
    def is_valid_image(self, image):
        """Check whether the downloaded image is valid, 
        by comparing the downloaded image with a NULL image returned by any unsuccessfully retrieval

        Bing tile system will return the same NULL image if the query quadkey is not existed in the Bing map database.
        
        Arguments:
            image {[Image]} -- [a Image type image to be valided]
        
        Returns:
            [boolean] -- [whether the image is valid]
        """

        if not os.path.exists('null.png'):
            nullimg = self.download_image('11111111111111111111')      # an invalid quadkey which will download a null jpeg from Bing tile system
            nullimg.save('./null.png')
        return not (image == Image.open('./null.png'))

    def max_resolution_imagery_retrieval(self):
        """The main aerial retrieval method

        It will firstly determine the appropriate level used to retrieve the image.
        The appropriate level should satisfy:
            1. All the tile image within the given bounding box at that level should all exist
            2. The retrieved image cannot exceed the maximum supported image size, which is 8192*8192 (Otherwise the image size will be too large if the bounding box is very large)
        
        Then for the given level, we can download each aerial tile image, and stitch them together.

        Lastly, we have to crop the image based on the given bounding box

        Returns:
            [boolean] -- [indicate whether the aerial image retrieval is successful]
        """

        for levl in range(self.maxZoom, 0, -1):
            pixelX1, pixelY1 = ts.latLongToPixelXY(self.upper_left[0], self.upper_left[1], levl)
            pixelX2, pixelY2 = ts.latLongToPixelXY(self.lower_right[0], self.lower_right[1], levl)

            pixelX1, pixelX2 = min(pixelX1, pixelX2), max(pixelX1, pixelX2)
            pixelY1, pixelY2 = min(pixelY1, pixelY2), max(pixelY1, pixelY2)

            
            #Bounding box's two coordinates coincide at the same pixel, which is invalid for an aerial image.
            #Raise error and directly return without retriving any valid image.
            if abs(pixelX1 - pixelX2) <= 1 or abs(pixelY1 - pixelY2) <= 1:
                print("Cannot find a valid aerial imagery for the given bounding box!")
                return

            if abs(pixelX1 - pixelX2) * abs(pixelY1 - pixelY2) > MAXSIZE:
                print("Current level {} results an image exceeding the maximum image size (8192 * 8192), will SKIP".format(levl))
                continue
            
            tileX1, tileY1 = ts.pixelXYToTileXY(pixelX1, pixelY1)
            tileX2, tileY2 = ts.pixelXYToTileXY(pixelX2, pixelY2)

            # Stitch the tile images together
            result = Image.new('RGB', ((tileX2 - tileX1 + 1) * self.tileSize, (tileY2 - tileY1 + 1) * self.tileSize))
            retrieve_sucess = False
            for tileY in range(tileY1, tileY2 + 1):
                retrieve_sucess, horizontal_image = self.horizontal_retrieval_and_stitch_image(tileX1, tileX2, tileY, levl)
                if not retrieve_sucess:
                    break
                result.paste(horizontal_image, (0, (tileY - tileY1) * self.tileSize))

            if not retrieve_sucess:
                continue

            # Crop the image based on the given bounding box
            leftup_cornerX, leftup_cornerY = ts.tileXYToPixelXY(tileX1, tileY1)
            retrieve_image = result.crop((pixelX1 - leftup_cornerX, pixelY1 - leftup_cornerY, \
                                        pixelX2 - leftup_cornerX, pixelY2 - leftup_cornerY))
            
            date_string = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
            
            print("Finish the aerial image retrieval, store the image aerialImage_{0}_{1}.jpeg in folder {2}".format(levl, date_string, self.tgtfolder))
            filename = os.path.join(self.tgtfolder, 'aerialImage_{0}_{1}.jpeg'.format(levl, date_string))
            retrieve_image.save(filename)
            return True
        return False    
            


    def horizontal_retrieval_and_stitch_image(self, tileX_start, tileX_end, tileY, level):
        """Horizontally retrieve tile images and then stitch them together,
        start from tileX_start and end at tileX_end, tileY will remain the same
        
        Arguments:
            tileX_start {[int]} -- [the starting tileX index]
            tileX_end {[int]} -- [the ending tileX index]
            tileY {[int]} -- [the tileY index]
            level {[int]} -- [level used to retrieve image]
        
        Returns:
            [boolean, Image] -- [whether such retrieval is successful; If successful, returning the stitched image, otherwise None]
        """

        imagelist = []
        for tileX in range(tileX_start, tileX_end + 1):
            quadkey = ts.tileXYToQuadKey(tileX, tileY, level)
            image = self.download_image(quadkey)
            if self.is_valid_image(image):
                imagelist.append(image)
            else:
                print("Cannot find tile image at level {0} for tile coordinate ({1}, {2})".format(level, tileX, tileY))
                return False, None
        result = Image.new('RGB', (len(imagelist) * self.tileSize, self.tileSize))
        for i, image in enumerate(imagelist):
            result.paste(image, (i * self.tileSize, 0))
        return True, result       

        
def main():
    
    try:
        args = sys.argv[1:]
    except IndexError:
        sys.exit('(Latitude, Longitude) coordinates must be input')
    if len(args) != 2:
        sys.exit('Please only input a coordinate pair for your central point.')
    
    try:
        lat, lon = float(args[0]), float(args[1])
    except ValueError:
        sys.exit('Latitude and longitude must be float type')
    

    # Retrieve the aerial image
    img = BingAerialImage(lat, lon)
    if img.max_resolution_imagery_retrieval():
        print("Successfully retrieve the image with maximum resolution!")
    else:
        print("Cannot retrieve the desired image! (Possible reason: expected tile image does not exist.)")


if __name__ == '__main__':
    main()

        

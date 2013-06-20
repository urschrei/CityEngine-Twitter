# -*- coding: utf-8 -*-
"""
Created on 2013-06-04

@author: Flora Roumpani (flora.roumpani.11@ucl.ac.uk)
@author: Stephan Hügel (stephan.hugel.12@ucl.ac.uk)
http://www.bartlett.ucl.ac.uk/casa

"""
import sys
import datetime
import traceback
import math
sys.path.append("C:/Users/flora/pythonpackages")
import tweepy
from scripting import *

# get a CityEngine instance
ce = CE()

""" fill name of shapes to analyse """
name = 'buildings_tq_small'
countalltweets = 0
lotposXa = []
lotposYa = []
shapeslist = []
zipped = []


def bng(input_lat, input_lon):
    """
    Convert lat and long to BNG
    Expects two floats as input
    Returns a tuple of Easting, Northing floats
    Accurate to ~5m

    For testing purposes:
    input: 51.44533267, -0.32824866
    output: 516275.97337480687, 173142.1442810801

    Entirely Based on code by Hannah Fry (CASA):
    hannahfry.co.uk/2012/02/01/converting-british-national-grid-to-latitude-and-longitude-ii/

    """
    # simple bounds checking
    if not all([0 <= input_lat <= 90, -180 <= input_lon <= 180]):
        raise Exception(
            "input_lat should be between 0 and 90, input_lon should be between -180 and 80")
    # Convert input to degrees
    lat_1 = input_lat * math.pi / 180
    lon_1 = input_lon * math.pi / 180
    # The GSR80 semi-major and semi-minor axes used for WGS84 (m)
    a_1, b_1 = 6378137.000, 6356752.3141
    # The eccentricity (squared) of the GRS80 ellipsoid
    e2_1 = 1 - (b_1 * b_1) / (a_1 * a_1)
    # Transverse radius of curvature
    nu_1 = a_1 / math.sqrt(1 - e2_1 * math.sin(lat_1) ** 2)
    # Third spherical coordinate is 0, in this case
    H = 0
    x_1 = (nu_1 + H) * math.cos(lat_1) * math.cos(lon_1)
    y_1 = (nu_1 + H) * math.cos(lat_1) * math.sin(lon_1)
    z_1 = ((1 - e2_1) * nu_1 + H) * math.sin(lat_1)

    # Perform Helmert transform (to go between Airy 1830 (_1) and GRS80 (_2))
    s = 20.4894 * 10 ** -6
    # The translations along x,y,z axes respectively
    tx, ty, tz = -446.448, 125.157, -542.060
    # The rotations along x,y,z respectively, in seconds
    rxs, rys, rzs = -0.1502, -0.2470, -0.8421
    # In radians
    rx, ry, rz = \
        rxs * math.pi / (180 * 3600.),\
        rys * math.pi / (180 * 3600.),\
        rzs * math.pi / (180 * 3600.)
    x_2 = tx + (1 + s) * x_1 + (-rz) * y_1 + (ry) * z_1
    y_2 = ty + (rz) * x_1 + (1 + s) * y_1 + (-rx) * z_1
    z_2 = tz + (-ry) * x_1 + (rx) * y_1 + (1 + s) * z_1

    # The GSR80 semi-major and semi-minor axes used for WGS84 (m)
    a, b = 6377563.396, 6356256.909
    # The eccentricity of the Airy 1830 ellipsoid
    e2 = 1 - (b * b) / (a * a)
    p = math.sqrt(x_2 ** 2 + y_2 ** 2)
    # Initial value
    lat = math.atan2(z_2, (p * (1 - e2)))
    latold = 2 * math.pi

    # Latitude is obtained by an iterative procedure
    while abs(lat - latold) > 10 ** -16:
        lat, latold = latold, lat
        nu = a / math.sqrt(1 - e2 * math.sin(latold) ** 2)
        lat = math.atan2(z_2 + e2 * nu * math.sin(latold), p)

    lon = math.atan2(y_2, x_2)
    H = p / math.cos(lat) - nu
    # Scale factor on the central meridian
    F0 = 0.9996012717
    # Latitude of true origin (radians)
    lat0 = 49 * math.pi / 180
    # Longtitude of true origin and central meridian (radians)
    lon0 = -2 * math.pi / 180
    # Northing & easting of true origin (m)
    N0, E0 = -100000, 400000
    n = (a - b) / (a + b)
    # Meridional radius of curvature
    rho = a * F0 * (1-e2) * (1 - e2 * math.sin(lat) ** 2) ** (-1.5)
    eta2 = nu * F0 / rho - 1

    M1 = (1 + n + (5/4) * n ** 2 + (5 / 4) * n ** 3) \
        * (lat - lat0)
    M2 = (3 * n + 3 * n ** 2 + (21 / 8) * n ** 3) \
        * math.sin(lat - lat0) * math.cos(lat + lat0)
    M3 = ((15 / 8) * n ** 2 + (15 / 8) * n ** 3) \
        * math.sin(2 * (lat-lat0)) * math.cos(2 * (lat + lat0))
    M4 = (35 / 24) * n ** 3 * math.sin(3 * (lat - lat0)) \
        * math.cos(3 * (lat + lat0))

    M = b * F0 * (M1 - M2 + M3 - M4)

    I = M + N0
    II = nu * F0 * math.sin(lat) * \
        math.cos(lat) / 2
    III = nu * F0 * math.sin(lat) * \
        math.cos(lat) ** 3 * (5 - math.tan(lat) ** 2 + 9 * eta2) / 24
    IIIA = nu * F0 * math.sin(lat) * \
        math.cos(lat) ** 5 * (61 - 58 * math.tan(lat) ** 2 + math.tan(lat) ** 4) / 720
    IV = nu * F0 * math.cos(lat)
    V = nu * F0 * \
        math.cos(lat) ** 3 * (nu / rho - math.tan(lat) ** 2) / 6
    VI = nu * F0 * math.cos(lat) ** 5 * \
        (5 - 18 * math.tan(lat) ** 2 + math.tan(lat) ** 4 + 14 * eta2 - 58 * eta2 * math.tan(lat) ** 2) / 120

    N = I + II * (lon - lon0) \
        ** 2 + III * (lon - lon0) ** 4 + IIIA * (lon - lon0) ** 6
    E = E0 + IV * (lon - lon0) + V * (lon - lon0) \
        ** 3 + VI * (lon - lon0) ** 5
    return E, N


Shapes = ce.getObjectsFrom(ce.scene, ce.withName(name))
# zone cluster size
maxdistance = ce.getAttribute(Shapes[0], 'maxdistance')
# maximum allowed height
maxHGT = ce.getAttribute(Shapes[0], 'maxHGT')
# tweet step
twitHGT = ce.getAttribute(Shapes[0], 'twitHGT')

for i in range(len(Shapes)):
    # gets the position of all objects in scene called Lot1
    lotpos = ce.getPosition(Shapes[i])
    lotposX = lotpos[0]
    lotposY = lotpos[2]
    lotposXa.append(lotposX)
    lotposYa.append(lotposY)


# Twitter API keys
con_key = "7b1D8yCYcmCG56nNbPEw"
con_secret = "UwNDO8PW6J0S8vyLi9LlecVy9WOXrYEdJWmzVES3k"
acc_key = "372313985-odzBYBZsjQm2ZUZl5PDKeqySQKNNTZyP66UfrUBt"
acc_secret = "ssJrpET7ecQsPm8mIkWobDqSRbVftvIk1969X0BPU"


class StreamWatcherListener(tweepy.StreamListener):
    """ Watch the stream of an app, and respond to stream events """

    def __init__(self):
        super(StreamWatcherListener, self).__init__()

    def on_status(self, status):

        if status.coordinates:
            point = status.coordinates['coordinates']
            point[0], point[1] = point[1], point[0]
            global countalltweets
            countalltweets += 1
            # merging layers
            E, N = bng(point[0], point[1])
            N = -N
            for i in range(len(Shapes)):
                    # finds distance between the original object and every object in the scene
                    distance = math.sqrt(
                        (E - lotposXa[i]) *
                        (E - lotposXa[i]) +
                        (N - lotposYa[i]) *
                        (N - lotposYa[i]))
                    if distance < maxdistance:
                        # even odd rule to check whether a point falls within a polygon
                        c = False
                        shapeslist = ce.getVertices(Shapes[i])
                        filtered_shapes = [coord for coord in shapeslist if coord]
                        global zipped
                        zipped = zip(filtered_shapes[0::2], filtered_shapes[1::2])
                        jj = len(zipped) - 1
                        for ii in range(len(zipped)):
                            if (((zipped[ii][1] > N) != (zipped[jj][1] > N)) and
                                (E < (zipped[jj][0] - zipped[ii][0]) *
                                (N - (zipped[ii][1])) / ((zipped[jj][1]) -
                                (zipped[ii][1])) + zipped[ii][0])):
                                    c = not c
                            jj = ii
                        if c is True:
                            count_t1 = ce.getAttribute(Shapes[i], 'count_t')
                            ce.setAttribute(Shapes[i], 'count_t', count_t1 + 1)
                            hgt1 = ce.getAttribute(Shapes[i], 'HGT')
                            if hgt1 < maxHGT:
                                    ce.setAttribute(
                                        Shapes[i],
                                        'HGT',
                                        (hgt1 + ((maxHGT - hgt1) / maxHGT) * twitHGT))
                                    ce.generateModels(Shapes[i])
                            else:
                                hgt1 = maxHGT


def on_error(self, status_code):
        """ Echo any errors """
        print 'An error has occured! Status code = %s' % status_code
        if status_code == 420:
            print 'Exiting due to auth error - we have to respect a 420 error'
            raise
        # keep stream alive
        return True


def on_timeout(self):
        """ Echo a timeout """
        print 'Snoozing Zzzzzz'


def main():
    """ Main function """
    print 'Now monitoring filtered stream - %s' % datetime.datetime.now()

    def authorise(*args):
        """
        Tweepy OAuth dance
        Accepts: consumer key, secret; access key, secret

        """
        auth = tweepy.OAuthHandler(
            args[0],
            args[1])
        auth.set_access_token(
            args[2],
            args[3])
        return auth

    twitter = authorise(con_key, con_secret, acc_key, acc_secret)
    swl = StreamWatcherListener()
    stream = tweepy.streaming.Stream(
        twitter,
        swl,
        timeout=None,
        secure=True)
    stream.filter(locations=[-0.5630, 51.2613, 0.2804, 51.6860])
    print 'Now monitoring filtered stream - %s' % datetime.datetime.now()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        # actually raise these so it exits cleanly
        raise
    except Exception, error:
        # all other exceptions, so display the error
        print "Stack trace:\n", traceback.print_exc(file=sys.stdout)
    else:
        pass
    finally:
        # exit cleanly once we've done everything else
        print 'Total no. of Tweets:', countalltweets
        print 'End streaming at - %s' % datetime.datetime.now()
        sys.exit()

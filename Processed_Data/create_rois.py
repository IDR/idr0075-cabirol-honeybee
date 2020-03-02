import os
import sys
import pandas
import omero
from omero.gateway import BlitzGateway, ColorHolder
from omero.rtypes import rdouble, rint


# Pixel sizes:
z_size = 0.5
z_planes = 101

x_size = 0.3438
x_max = 512

y_size = 0.3438
y_max = 512

# ROI color:
r = 0
g = 255
b = 255
a = 255


def printusage():
    print('''
Takes a csv file with no header and three columns where each
row[0] = x, row[1] = y and row[2] = z are coordinates of a point
(in micrometers). Converts x, y to pixel coordinates and z to
z plane indices and creates a point ROI on the given image for
each point. Adjust the x,y,z pixel sizes in the script!

Usage: python create_rois.py [path to coordinates.csv] [Image ID]

Set the environment variables OMERO_USER, OMERO_PASSWORD, OMERO_HOST.
    ''')
    sys.exit(1)


def add_point(us, img, x, y, z):
    """ Adds a point ROI to the given image
    Args:
    us The UpdateService
    img The image (ImageWrapper)
    x x (in pixels)
    y y (in pixels)
    z z plane index
    """
    p = omero.model.PointI()
    p.x = rdouble(x)
    p.y = rdouble(y)
    p.theZ = rint(z)
    ch = ColorHolder.fromRGBA(r, g, b, a)
    p.setStrokeColor(rint(ch.getInt()))
    roi = omero.model.RoiI()
    roi.setImage(img._obj)
    roi.addShape(p)
    us.saveAndReturnObject(roi)


def calc_pos(x, y, z):
    """ Calculates the position in pixels / z plane index
    Args:
    x x (in micrometers)
    y y (in micrometers)
    z z (in micrometers)
    Returns:
    x, y (pixels), z (z plane index) (tuple)
    """
    x_pix = round(x / x_size)
    if x_pix >= x_max:
        raise Exception("x coordinate out of bounds")

    y_pix = round(y / y_size)
    if y_pix >= y_max:
        raise Exception("y coordinate out of bounds")

    z_index = round(z / z_size)
    if z_index >= z_planes:
        raise Exception("z_index out of bounds")

    return x_pix, y_pix, z_index


if len(sys.argv) < 3:
    printusage()
else:
    csv_file = sys.argv[1]
    image_id = sys.argv[2]

host = os.environ.get('OMERO_HOST', 'localhost')
port = int(os.environ.get('OMERO_PORT', '4064'))

conn = BlitzGateway(os.environ.get('OMERO_USER', 'NA'),
                    os.environ.get('OMERO_PASSWORD', 'NA'),
                    host=host, port=port)
conn.connect()

us = conn.getUpdateService()
img = conn.getObject("Image", int(image_id))

df = pandas.read_csv(csv_file, header=None)
total = df.size / 3
for index, row in df.iterrows():
    x, y, z = calc_pos(row[0], row[1], row[2])
    add_point(us, img, x, y, z)
    print("{}/{} done".format((index+1), total))

conn.close()

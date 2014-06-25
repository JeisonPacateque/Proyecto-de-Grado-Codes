# -*- coding: utf-8 -*-
"""
Created on Tue Jun 10 10:03:34 2014

@author: santiago
"""

import numpy as np
#import dicom
#from matplotlib import pyplot as pp
#
#dicom_image = dicom.read_file('/home/santiago/Proyecto-de-Grado-Codes/samples/6/sample_120.dcm')
#matrix = dicom_image.pixel_array[35:485, 35:485]

def sector_mask(shape,centre,radius,angle_range):
    """
    Return a boolean mask for a circular sector. The start/stop angles in  
    `angle_range` should be given in clockwise order.
    """

    x,y = np.ogrid[:shape[0],:shape[1]]
    cx,cy = centre
    tmin,tmax = np.deg2rad(angle_range)

    # ensure stop angle > start angle
    if tmax < tmin:
            tmax += 2*np.pi

    # convert cartesian --> polar coordinates
    r2 = (x-cx)*(x-cx) + (y-cy)*(y-cy)
    theta = np.arctan2(x-cx,y-cy) - tmin

    # wrap angles between 0 and 2*pi
    theta %= (2*np.pi)

    # circular mask
    circmask = r2 <= radius*radius

    # angular mask
    anglemask = theta <= (tmax-tmin)

    return circmask*anglemask
    
    
#print matrix.shape    
#mask = sector_mask(matrix.shape,(225,225),225,(0,360))
#matrix[~mask] = 555
#print np.count_nonzero(matrix==555)
#pp.imshow(matrix)
#pp.show()
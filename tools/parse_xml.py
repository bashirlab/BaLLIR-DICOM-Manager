# standard imports
from scipy import interpolate
from ast import literal_eval
import numpy as np

# custom imports



def getROIcoords(roi):

    # get index of ROI
    ind = int(roi['integer'][1])
    # get coordinate data of ROI
    x = roi['array']['dict']['array'][1]['string']
    # convert string coordinates to tuples
    coords = [literal_eval(coord) for coord in x]
    # parse out x and y and make closed loop
    x = [i[0] for i in coords] + [coords[0][0]]
    y = [i[1] for i in coords] + [coords[0][1]]
    # apply parametric spline interpolation
    tck, _ = interpolate.splprep([x,y], s=0, per=True)
    x, y = interpolate.splev(np.linspace(0,1,500), tck)
    
    return ind, x, y

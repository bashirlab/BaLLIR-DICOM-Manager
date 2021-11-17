# standard imports

import numpy as np
import imageio
import os

# custom imports

from shortcuts import *


# GENERATE RGB image

def generateRGB(arr, pred):
        
    arr /= np.amax(arr)
    arr = arr[np.newaxis, ...]
    pred = pred[np.newaxis, ...]
    pred = arr + pred*0.3
    pred /= np.amax(pred)
    RGB = np.concatenate((arr, arr, arr), axis = 0)
    RGB_draw = np.concatenate((arr, arr, pred), axis = 0)
    RGB = np.swapaxes(RGB, 0, 3)
    RGB_draw = np.swapaxes(RGB_draw, 0, 3)
    RGB = np.concatenate((RGB,RGB_draw), axis = 2)
    
    return RGB


# SAVE QC image as PNG in DIRECTORY

def saveQC(QC, dir_save, overwrite = False):
    
    buildDir(dir_save, overwrite = overwrite)

    for i in range(QC.shape[0]):
        loc_save = os.path.join(dir_save, str(i)+'.png')
        imageio.imwrite(loc_save, QC[i,...])
    
    return

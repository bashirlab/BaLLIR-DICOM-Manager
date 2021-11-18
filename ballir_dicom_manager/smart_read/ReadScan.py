import os
from abc import ABC, abstractmethod

import cv2
from glob import glob
import numpy as np
from matplotlib import pyplot as plt


class ReadScan(ABC):
    """Base class for reading and displaying file."""

    def __init__(self):
        pass    
    
    def window_level(self, arr, window_center, window_width, rescale_intercept, rescale_slope):
        """Applying window/level to input array."""
        lower_limit = window_center - (window_width/2)
        upper_limit = window_center + (window_width/2)

        hounsfield_img = (arr*rescale_slope) + rescale_intercept
        clipped_img = np.clip(hounsfield_img, lower_limit, upper_limit)
        return (clipped_img/window_width) - (lower_limit/window_width)
    
    
    def return_window_level_attributes(self, tmp_dcm):

        attr = {'WindowCenter': 50.0, 'WindowWidth': 400.0, 'RescaleIntercept': 0.0, 'RescaleSlope': 1.0}

        for key, value in attr.items():
            if hasattr(tmp_dcm, key):
                try:
                    attr[key] = float(getattr(tmp_dcm, key))
                except:
                    attr[key] = float(getattr(tmp_dcm, key)[0])
#             else:
#                 print('MISSING: ', key)

        wc, window_width, rescale_intercept, rescale_slope = attr.values()
        return wc, window_width, rescale_intercept, rescale_slope
    
    
    def getWinLevAttr_json(self, tmp_json):
        
        attr = {'00281050': 50.0, '00281051': 400.0, '00281052': -1024.0, '00281053': 1.0}

        for key, value in attr.items():
            if key in tmp_json.keys():
                try:
                    attr[key] = float(tmp_json[key]['Value'])
                except:
                    attr[key] = float(tmp_json[key]['Value'][0])
#             else:
#                 print('MISSING: ', key)

        wc, window_width, rescale_intercept, rescale_slope = attr.values()
        return wc, window_width, rescale_intercept, rescale_slope
 

        for attr_num, attr_name in enumerate(attr):
            if attr_name in tmp_json.keys():    
                try:
                    attr_vars[attr_num] = float(tmp_json[attr_name]['Value'])
                except:
                     attr_vars[attr_num] = float(tmp_json[attr_name]['Value'][0])
#             else:
#                 print('MISSING: ', attr_name)
        print(str(wc) + ' ' + str(window_width) + ' ' + str(rescale_intercept) + ' ' + str(rescale_slope))
        return wc, window_width, rescale_intercept, rescale_slope
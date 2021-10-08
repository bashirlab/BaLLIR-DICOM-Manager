from glob import glob
import numpy as np
import os
try:
    import cv2
except:
    from subprocess import STDOUT, check_call
    check_call(['apt-get', 'update'],
         stdout=open(os.devnull,'wb'), stderr=STDOUT) 
    check_call(['apt-get', 'install', 'ffmpeg', 'libsm6', 'libxext6', '-y'],
         stdout=open(os.devnull,'wb'), stderr=STDOUT) 
    import cv2
from matplotlib import pyplot as plt


class ReadScan():
    
    def __init__(self):
        pass    
    
    def winLev(self, arr, wc, ww, ri, rs):

        lower_limit = wc - (ww/2)
        upper_limit = wc + (ww/2)

        hounsfield_img = (arr*rs) + ri
        clipped_img = np.clip(hounsfield_img, lower_limit, upper_limit)
        windowLevel = (clipped_img/ww) - (lower_limit/ww)

        return windowLevel
    
    
    def getWinLevAttr_dcm(self, tmp_dcm):

        attr = {'WindowCenter': 50.0, 'WindowWidth': 400.0, 'RescaleIntercept': 0.0, 'RescaleSlope': 1.0}

        for key, value in attr.items():
            if hasattr(tmp_dcm, key):
                try:
                    attr[key] = float(getattr(tmp_dcm, key))
                except:
                    attr[key] = float(getattr(tmp_dcm, key)[0])
#             else:
#                 print('MISSING: ', key)

        wc, ww, ri, rs = attr.values()
        return wc, ww, ri, rs
    
    
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

        wc, ww, ri, rs = attr.values()
        return wc, ww, ri, rs
 

        for attr_num, attr_name in enumerate(attr):
            if attr_name in tmp_json.keys():    
                try:
                    attr_vars[attr_num] = float(tmp_json[attr_name]['Value'])
                except:
                     attr_vars[attr_num] = float(tmp_json[attr_name]['Value'][0])
#             else:
#                 print('MISSING: ', attr_name)
        print(str(wc) + ' ' + str(ww) + ' ' + str(ri) + ' ' + str(rs))
        return wc, ww, ri, rs
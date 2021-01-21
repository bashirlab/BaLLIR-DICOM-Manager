from ..tools.ManageDicom import ManageDicom
from glob import glob
import numpy as np
import pydicom as dcm
import os
import cv2
from matplotlib import pyplot as plt



def check_tags(files_dicom, list_tags): 

    dict_tags = {}
    dict_max = {}
    
    for tag in list_tags:
        count_tags = [getattr(file, tag) for file in files_dicom]
        unq_tags = set(count_tags); unq_tags = list(unq_tags)
        
        tmp_counts = []
        for unq in unq_tags:
            dict_tags[tag + '--' + str(unq)] = count_tags.count(unq)
            tmp_counts.append(count_tags.count(unq))
        dict_max[tag] = unq_tags[tmp_counts.index(max(tmp_counts))]
        
    for key, value in dict_tags.items():
        print(key.split('--'), ' : ', value)
#         [tag, val] = key.split('--')

    for key, value in dict_max.items():
        print('most frequent value for ', key, ' key: ', value) 
              
    return dict_tags, dict_max


class ReadDicom(ManageDicom):
    
    def __init__(self, filename, filter_tags = False, window_level = False):
        
        #add something to check for inconsistencies in dicom files...slice thickness, etc., 
        list_glob = glob(os.path.join(filename, '**/*.dcm'), recursive = True); list_glob.sort(); #list_glob.reverse()
        scan = [dcm.dcmread(file) for file in list_glob]
        
        #edit so if not filter it reads the full files, otherwise it stops before pixel values, then reads pixel values after filtering
        if filter_tags:
            dict_tags, dict_max = check_tags(scan, filter_tags)
            for tag in filter_tags:
                scan = [file for file in scan if getattr(file, tag) == dict_max[tag]]
        
        arr = np.array([file.pixel_array for file in scan]); arr = np.swapaxes(arr, 0, 2); arr = np.flip(arr, 1); arr = np.flip(arr, 2)
        window_center, window_width, rescale_intercept, rescale_slope = super().getWinLevAttr_dcm(scan[0])
        if window_level:
            arr = super().winLev(arr, window_center, window_width, rescale_intercept, rescale_slope)
            
        self.root_file = filename
        self.root_type = 'DICOM'
        #self.scan_type = 'MR', 'CT', etc.
        self.scan = scan
        self.arr = arr
        self.length = arr.shape[2]
        self.spacing = scan[0].PixelSpacing; self.spacing.append(scan[0].SliceThickness)
        self.range = [self.spacing[0] * self.arr.shape[0], self.spacing[1] * self.arr.shape[1], self.spacing[2] * self.arr.shape[2]]
        self.window_width = window_width
        self.window_center = window_center
        self.rescale_slope = rescale_slope
        self.rescale_intercept = rescale_intercept
        

        
    def orthoview(self, windowLevel = False):
        
        transverse = self.arr[..., int(self.arr.shape[2]/2)]
        transverse = cv2.resize(transverse, dsize = (int(self.range[1]), int(self.range[0])), interpolation = cv2.INTER_CUBIC); transverse = np.rot90(transverse)
        saggital = self.arr[int(self.arr.shape[0]/2), ...]
        saggital = cv2.resize(saggital, dsize = (int(self.range[2]), int(self.range[0])), interpolation = cv2.INTER_CUBIC); saggital = np.rot90(saggital)
        coronal = self.arr[:, int(self.arr.shape[1]/2), :] 
        coronal = cv2.resize(coronal, dsize = (int(self.range[2]), int(self.range[1])), interpolation = cv2.INTER_CUBIC); coronal = np.rot90(coronal)
        ims = [transverse, saggital, coronal]
        fig=plt.figure(figsize=(15, 15))
        for i in range(1, 4):
            fig.add_subplot(1, 3, i)
            plt.imshow(ims[i - 1],cmap = 'gray')
        plt.show()
        
